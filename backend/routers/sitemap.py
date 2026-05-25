import asyncio
import io
import os
import uuid
from datetime import datetime
from typing import Literal
from urllib.parse import urlparse, urlunparse

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from openpyxl.styles import Font
from pydantic import BaseModel
from sqlalchemy.orm import Session

import crud
import schemas
from database import SessionLocal, get_db
from services.sitemap_parser import SitemapParserError, parse_sitemap


router = APIRouter(prefix="/api/sitemap", tags=["sitemap"])


class _LoadJob(BaseModel):
    status: Literal["running", "done", "error"] = "running"
    found: int = 0
    total: int | None = None
    session_id: int | None = None
    error: str | None = None


LOAD_JOBS: dict[str, _LoadJob] = {}


def _get_sitemap_limit() -> int | None:
    raw_value = os.getenv("MAX_SITEMAP_URLS", "0").strip()
    if not raw_value:
        return None
    try:
        parsed = int(raw_value)
    except ValueError:
        return None
    return parsed if parsed > 0 else None


def _normalize_host_preserve_www(url: str, sitemap_url: str) -> str:
    sitemap_host = (urlparse(sitemap_url).netloc or "").lower()
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()

    if not sitemap_host.startswith("www."):
        return url

    bare_sitemap_host = sitemap_host[4:]
    if host != bare_sitemap_host:
        return url

    return urlunparse((parsed.scheme, sitemap_host, parsed.path, parsed.params, parsed.query, parsed.fragment))


def _normalize_entries_host(entries: list[dict[str, str | None]], sitemap_url: str) -> list[dict[str, str | None]]:
    normalized: list[dict[str, str | None]] = []
    for entry in entries:
        item = dict(entry)
        item["url"] = _normalize_host_preserve_www(entry["url"], sitemap_url)
        normalized.append(item)
    return normalized


async def _run_load_job(job_id: str, sitemap_url: str) -> None:
    job = LOAD_JOBS[job_id]
    db: Session = SessionLocal()
    try:
        def on_progress(found: int) -> None:
            job.found = found

        parsed_urls = await parse_sitemap(sitemap_url, limit=_get_sitemap_limit(), progress_callback=on_progress)
        if not parsed_urls:
            job.status = "error"
            job.error = "Sitemap parsed, but no URLs found"
            return

        parsed_urls = _normalize_entries_host(parsed_urls, sitemap_url)
        session = crud.create_scan_session(db, sitemap_url=sitemap_url)
        entries = crud.bulk_create_entries(db, session_id=session.id, entries=parsed_urls)

        job.status = "done"
        job.total = len(entries)
        job.found = len(entries)
        job.session_id = session.id
    except SitemapParserError as exc:
        job.status = "error"
        job.error = str(exc)
    except Exception as exc:  # noqa: BLE001
        job.status = "error"
        job.error = f"Unexpected error: {exc}"
    finally:
        db.close()


@router.post("/load/start", response_model=schemas.SitemapLoadStartResponse)
async def start_load_sitemap(payload: schemas.SitemapLoadRequest) -> schemas.SitemapLoadStartResponse:
    job_id = uuid.uuid4().hex
    LOAD_JOBS[job_id] = _LoadJob()
    asyncio.create_task(_run_load_job(job_id=job_id, sitemap_url=str(payload.url)))
    return schemas.SitemapLoadStartResponse(job_id=job_id, status="started")


@router.get("/load/progress", response_model=schemas.SitemapLoadProgressResponse)
def load_sitemap_progress(job_id: str = Query(...)) -> schemas.SitemapLoadProgressResponse:
    job = LOAD_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Load job not found")
    return schemas.SitemapLoadProgressResponse(
        job_id=job_id,
        status=job.status,
        found=job.found,
        total=job.total,
        session_id=job.session_id,
        error=job.error,
    )


@router.get("/load/result", response_model=schemas.SitemapLoadResponse)
def load_sitemap_result(job_id: str = Query(...), db: Session = Depends(get_db)) -> schemas.SitemapLoadResponse:
    job = LOAD_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Load job not found")
    if job.status == "running":
        raise HTTPException(status_code=409, detail="Load job is still running")
    if job.status == "error":
        raise HTTPException(status_code=400, detail=job.error or "Sitemap load failed")
    if not job.session_id:
        raise HTTPException(status_code=500, detail="Load job finished without session id")

    entries = crud.get_entries_by_session(db, job.session_id)
    return schemas.SitemapLoadResponse(session_id=job.session_id, urls=entries, total=len(entries))


@router.post("/load", response_model=schemas.SitemapLoadResponse)
async def load_sitemap(payload: schemas.SitemapLoadRequest, db: Session = Depends(get_db)) -> schemas.SitemapLoadResponse:
    try:
        parsed_urls = await parse_sitemap(str(payload.url), limit=_get_sitemap_limit())
    except SitemapParserError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not parsed_urls:
        raise HTTPException(status_code=400, detail="Sitemap parsed, but no URLs found")

    normalized_urls = _normalize_entries_host(parsed_urls, str(payload.url))
    session = crud.create_scan_session(db, sitemap_url=str(payload.url))
    entries = crud.bulk_create_entries(db, session_id=session.id, entries=normalized_urls)
    return schemas.SitemapLoadResponse(session_id=session.id, urls=entries, total=len(entries))


@router.get("/export")
def export_sitemap(session_id: int = Query(...), db: Session = Depends(get_db)) -> StreamingResponse:
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    entries = crud.get_entries_by_session(db, session_id)
    if not entries:
        raise HTTPException(status_code=404, detail="No URLs to export")

    data = [
        {
            "URL": entry.url,
            "Last Modified": entry.lastmod,
            "Priority": entry.priority,
            "Source Sitemap": entry.source_sitemap,
            "Title": entry.title,
        }
        for entry in entries
    ]
    df = pd.DataFrame(data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sitemap")
        ws = writer.book["Sitemap"]
        for cell in ws[1]:
            cell.font = Font(bold=True)
        for column_cells in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in column_cells)
            ws.column_dimensions[column_cells[0].column_letter].width = min(max_len + 2, 80)

    output.seek(0)
    domain = (urlparse(session.sitemap_url).netloc or "site").replace(":", "_")
    filename = f"sitemap_export_{domain}_{datetime.utcnow().strftime('%Y-%m-%d')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/session", response_model=schemas.SitemapLoadResponse)
def get_session_data(session_id: int = Query(...), db: Session = Depends(get_db)) -> schemas.SitemapLoadResponse:
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    entries = crud.get_entries_by_session(db, session_id)
    return schemas.SitemapLoadResponse(session_id=session_id, urls=entries, total=len(entries))


@router.get("/archive", response_model=schemas.ArchiveListResponse)
def get_archive(
    query: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> schemas.ArchiveListResponse:
    items, total = crud.get_archive_sessions(db, query=query, limit=limit, offset=offset)
    return schemas.ArchiveListResponse(items=[schemas.ArchiveSessionItem(**item) for item in items], total=total)


@router.get("/archive/{session_id}", response_model=schemas.SitemapLoadResponse)
def restore_archive_session(session_id: int, db: Session = Depends(get_db)) -> schemas.SitemapLoadResponse:
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    entries = crud.get_entries_by_session(db, session_id)
    return schemas.SitemapLoadResponse(session_id=session_id, urls=entries, total=len(entries))
