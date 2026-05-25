import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import crud
import schemas
from database import get_db
from services.title_scanner import create_task_id, get_scan_runtime, run_title_scan
from services.url_tester import create_test_task_id, get_url_test_runtime, run_url_test


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
    progress = crud.get_test_progress(db, session_id)
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
        mode="test_urls",
    )
