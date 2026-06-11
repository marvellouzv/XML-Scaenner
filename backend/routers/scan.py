import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import crud
import schemas
from database import get_db
from services.title_scanner import create_task_id, get_scan_runtime, run_title_scan
from services.url_tester import cancel_url_test, create_test_task_id, get_url_test_runtime, run_url_test, run_url_test_for_entries


router = APIRouter(prefix="/api/scan", tags=["scan"])


@router.post("/titles", response_model=schemas.ScanStartResponse)
async def scan_titles(payload: schemas.ScanStartRequest, db: Session = Depends(get_db)) -> schemas.ScanStartResponse:
    session = crud.get_session(db, payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    entries = crud.get_entries_by_session(db, payload.session_id)
    if not entries:
        raise HTTPException(status_code=400, detail="No URLs found for scanning")

    task_id = create_task_id(payload.session_id)
    asyncio.create_task(run_title_scan(payload.session_id))
    return schemas.ScanStartResponse(task_id=task_id, status="started")


@router.post("/test-urls", response_model=schemas.ScanStartResponse)
async def test_urls(payload: schemas.ScanStartRequest, db: Session = Depends(get_db)) -> schemas.ScanStartResponse:
    session = crud.get_session(db, payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    entries = crud.get_entries_by_session(db, payload.session_id)
    if not entries:
        raise HTTPException(status_code=400, detail="No URLs found for testing")

    task_id = create_test_task_id(payload.session_id)
    asyncio.create_task(run_url_test(payload.session_id))
    return schemas.ScanStartResponse(task_id=task_id, status="started")


@router.post("/test-urls/retest", response_model=schemas.ScanStartResponse)
async def retest_urls(payload: schemas.ScanRetestRequest, db: Session = Depends(get_db)) -> schemas.ScanStartResponse:
    session = crud.get_session(db, payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not payload.entry_ids:
        raise HTTPException(status_code=400, detail="No entry_ids provided for retest")

    entries = crud.get_entries_by_ids(db, session_id=payload.session_id, entry_ids=payload.entry_ids)
    if not entries:
        raise HTTPException(status_code=400, detail="No matching URLs found for retest")

    crud.reset_selected_entries_test_statuses(db, session_id=payload.session_id, entry_ids=payload.entry_ids)
    task_id = create_test_task_id(payload.session_id)
    asyncio.create_task(run_url_test_for_entries(payload.session_id, [entry.id for entry in entries]))
    return schemas.ScanStartResponse(task_id=task_id, status="started")


@router.post("/test-urls/pause", response_model=schemas.ScanStartResponse)
async def pause_test_urls(payload: schemas.ScanStartRequest, db: Session = Depends(get_db)) -> schemas.ScanStartResponse:
    session = crud.get_session(db, payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "testing":
        raise HTTPException(status_code=409, detail="TEST URL is not running")

    cancel_url_test(payload.session_id)
    return schemas.ScanStartResponse(task_id=f"pause-{payload.session_id}", status="started")


@router.get("/progress", response_model=schemas.ScanProgressResponse)
def scan_progress(session_id: int, db: Session = Depends(get_db)) -> schemas.ScanProgressResponse:
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    runtime = get_scan_runtime(session_id)
    if session.status == "scanning" and runtime is None:
        interrupted = crud.mark_pending_entries_as_error(
            db,
            session_id=session_id,
            reason="Scan interrupted (server restart). Run scan again.",
        )
        crud.mark_session_status(db, session_id=session_id, status="done")
        runtime = {
            "phase": "interrupted",
            "message": "Сканирование было прервано из-за перезапуска сервера.",
            "decision": f"Пометил {interrupted} URL как error. Нажмите ПОВТОРИТЬ для нового обхода.",
            "round": None,
            "total_rounds": None,
            "current_concurrency": None,
            "current_delay": None,
            "pending_urls": interrupted,
        }

    progress = crud.get_progress(db, session_id)
    refreshed_session = crud.get_session(db, session_id)
    status = "done" if (refreshed_session and refreshed_session.status == "done") else "running"
    return schemas.ScanProgressResponse(
        total=progress["total"],
        scanned=progress["scanned"],
        errors=progress["errors"],
        error_breakdown=progress["error_breakdown"],
        status=status,
        runtime_phase=runtime["phase"] if runtime else None,
        runtime_message=runtime["message"] if runtime else None,
        runtime_decision=runtime["decision"] if runtime else None,
        runtime_round=runtime["round"] if runtime else None,
        runtime_total_rounds=runtime["total_rounds"] if runtime else None,
        runtime_concurrency=runtime["current_concurrency"] if runtime else None,
        runtime_delay=runtime["current_delay"] if runtime else None,
        runtime_pending_urls=runtime["pending_urls"] if runtime else None,
        mode="titles",
    )


@router.get("/test-progress", response_model=schemas.ScanProgressResponse)
def test_progress(session_id: int, db: Session = Depends(get_db)) -> schemas.ScanProgressResponse:
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    runtime = get_url_test_runtime(session_id)
    if session.status == "testing" and runtime is None:
        has_pending = crud.has_pending_test_entries(db, session_id)
        recovered_status = "loaded" if has_pending else "done"
        crud.mark_session_status(db, session_id=session_id, status=recovered_status)
        runtime = {
            "phase": "interrupted",
            "message": "Тестирование было прервано (например, перезапуск сервера).",
            "decision": "Нажмите RESUME TEST для продолжения с оставшихся URL." if has_pending else "Все URL уже обработаны.",
            "round": None,
            "total_rounds": None,
            "current_concurrency": None,
            "current_delay": None,
            "pending_urls": None,
        }

    progress = crud.get_test_progress(db, session_id)
    refreshed_session = crud.get_session(db, session_id)
    status = "running" if (refreshed_session and refreshed_session.status == "testing") else "done"
    return schemas.ScanProgressResponse(
        total=progress["total"],
        scanned=progress["scanned"],
        errors=progress["errors"],
        error_breakdown=progress["error_breakdown"],
        status=status,
        runtime_phase=runtime["phase"] if runtime else None,
        runtime_message=runtime["message"] if runtime else None,
        runtime_decision=runtime["decision"] if runtime else None,
        runtime_round=runtime["round"] if runtime else None,
        runtime_total_rounds=runtime["total_rounds"] if runtime else None,
        runtime_concurrency=runtime["current_concurrency"] if runtime else None,
        runtime_delay=runtime["current_delay"] if runtime else None,
        runtime_pending_urls=runtime["pending_urls"] if runtime else None,
        mode="test_urls",
    )
