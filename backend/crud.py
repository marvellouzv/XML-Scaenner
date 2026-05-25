import time

from sqlalchemy import case, func
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

import models


def create_scan_session(db: Session, sitemap_url: str) -> models.ScanSession:
    session = models.ScanSession(sitemap_url=sitemap_url, status="loaded")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def bulk_create_entries(db: Session, session_id: int, entries: list[dict[str, str | None]]) -> list[models.SitemapEntry]:
    db_entries = [
        models.SitemapEntry(
            session_id=session_id,
            url=entry["url"],
            lastmod=entry.get("lastmod"),
            changefreq=entry.get("changefreq"),
            priority=entry.get("priority"),
            source_sitemap=entry.get("source_sitemap"),
            scan_status="pending",
        )
        for entry in entries
    ]
    db.add_all(db_entries)
    db.commit()
    for entry in db_entries:
        db.refresh(entry)
    return db_entries


def get_session(db: Session, session_id: int) -> models.ScanSession | None:
    return db.query(models.ScanSession).filter(models.ScanSession.id == session_id).first()


def get_entries_by_session(db: Session, session_id: int) -> list[models.SitemapEntry]:
    return db.query(models.SitemapEntry).filter(models.SitemapEntry.session_id == session_id).all()


def mark_session_status(db: Session, session_id: int, status: str) -> None:
    session = get_session(db, session_id)
    if session:
        session.status = status
        db.commit()


def mark_pending_entries_as_error(db: Session, session_id: int, reason: str) -> int:
    entries = (
        db.query(models.SitemapEntry)
        .filter(models.SitemapEntry.session_id == session_id, models.SitemapEntry.scan_status == "pending")
        .all()
    )
    for entry in entries:
        entry.scan_status = "error"
        entry.scan_error = reason
    db.commit()
    return len(entries)


def reset_entry_scan_statuses(db: Session, session_id: int) -> None:
    entries = db.query(models.SitemapEntry).filter(models.SitemapEntry.session_id == session_id).all()
    for entry in entries:
        entry.scan_status = "pending"
        entry.title = None
        entry.scan_error = None
    db.commit()


def reset_entry_test_statuses(db: Session, session_id: int) -> None:
    entries = db.query(models.SitemapEntry).filter(models.SitemapEntry.session_id == session_id).all()
    for entry in entries:
        entry.test_status = "pending"
        entry.test_error = None
        entry.test_http_status = None
        entry.test_response_time_ms = None
    db.commit()


def update_entry_title(db: Session, entry_id: int, title: str | None, scan_status: str, scan_error: str | None = None) -> None:
    for attempt in range(5):
        try:
            entry = db.query(models.SitemapEntry).filter(models.SitemapEntry.id == entry_id).first()
            if entry:
                entry.title = title
                entry.scan_status = scan_status
                entry.scan_error = scan_error
                db.commit()
            return
        except OperationalError:
            db.rollback()
            if attempt == 4:
                raise
            time.sleep(0.2 * (attempt + 1))


def update_entry_test_result(
    db: Session,
    entry_id: int,
    test_status: str,
    test_http_status: int | None,
    test_response_time_ms: int | None,
    test_error: str | None = None,
) -> None:
    for attempt in range(5):
        try:
            entry = db.query(models.SitemapEntry).filter(models.SitemapEntry.id == entry_id).first()
            if entry:
                entry.test_status = test_status
                entry.test_http_status = test_http_status
                entry.test_response_time_ms = test_response_time_ms
                entry.test_error = test_error
                db.commit()
            return
        except OperationalError:
            db.rollback()
            if attempt == 4:
                raise
            time.sleep(0.2 * (attempt + 1))


def get_progress(db: Session, session_id: int) -> dict[str, int | dict[str, int]]:
    total = db.query(func.count(models.SitemapEntry.id)).filter(models.SitemapEntry.session_id == session_id).scalar() or 0
    scanned = (
        db.query(func.count(models.SitemapEntry.id))
        .filter(models.SitemapEntry.session_id == session_id, models.SitemapEntry.scan_status.in_(["done", "error"]))
        .scalar()
        or 0
    )
    errors = (
        db.query(func.count(models.SitemapEntry.id))
        .filter(models.SitemapEntry.session_id == session_id, models.SitemapEntry.scan_status == "error")
        .scalar()
        or 0
    )
    raw_breakdown = (
        db.query(models.SitemapEntry.scan_error, func.count(models.SitemapEntry.id))
        .filter(models.SitemapEntry.session_id == session_id, models.SitemapEntry.scan_status == "error")
        .group_by(models.SitemapEntry.scan_error)
        .all()
    )
    error_breakdown: dict[str, int] = {}
    for error_text, count in raw_breakdown:
        key = (error_text or "Unknown error").strip()
        error_breakdown[key] = count

    return {"total": total, "scanned": scanned, "errors": errors, "error_breakdown": error_breakdown}


def get_test_progress(db: Session, session_id: int) -> dict[str, int | dict[str, int]]:
    total = db.query(func.count(models.SitemapEntry.id)).filter(models.SitemapEntry.session_id == session_id).scalar() or 0
    scanned = (
        db.query(func.count(models.SitemapEntry.id))
        .filter(models.SitemapEntry.session_id == session_id, models.SitemapEntry.test_status.in_(["done", "error"]))
        .scalar()
        or 0
    )
    errors = (
        db.query(func.count(models.SitemapEntry.id))
        .filter(models.SitemapEntry.session_id == session_id, models.SitemapEntry.test_status == "error")
        .scalar()
        or 0
    )
    raw_breakdown = (
        db.query(models.SitemapEntry.test_error, func.count(models.SitemapEntry.id))
        .filter(models.SitemapEntry.session_id == session_id, models.SitemapEntry.test_status == "error")
        .group_by(models.SitemapEntry.test_error)
        .all()
    )
    error_breakdown: dict[str, int] = {}
    for error_text, count in raw_breakdown:
        key = (error_text or "Unknown error").strip()
        error_breakdown[key] = count

    return {"total": total, "scanned": scanned, "errors": errors, "error_breakdown": error_breakdown}


def get_archive_sessions(
    db: Session,
    query: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict[str, int | str]], int]:
    base_query = db.query(models.ScanSession)
    if query:
        like_query = f"%{query.strip()}%"
        base_query = base_query.join(models.SitemapEntry).filter(models.SitemapEntry.url.ilike(like_query)).distinct()

    total = base_query.count()
    sessions = base_query.order_by(models.ScanSession.created_at.desc()).offset(offset).limit(limit).all()
    if not sessions:
        return [], total

    session_ids = [session.id for session in sessions]
    like_query = f"%{query.strip()}%" if query else None

    rows = (
        db.query(
            models.ScanSession.id.label("session_id"),
            models.ScanSession.sitemap_url.label("sitemap_url"),
            models.ScanSession.created_at.label("created_at"),
            models.ScanSession.status.label("status"),
            func.count(models.SitemapEntry.id).label("total_urls"),
            func.sum(case((models.SitemapEntry.scan_status == "done", 1), else_=0)).label("title_done"),
            func.sum(case((models.SitemapEntry.scan_status == "error", 1), else_=0)).label("title_errors"),
            func.sum(case((models.SitemapEntry.test_status == "done", 1), else_=0)).label("test_done"),
            func.sum(case((models.SitemapEntry.test_status == "error", 1), else_=0)).label("test_errors"),
            func.sum(case((models.SitemapEntry.url.ilike(like_query), 1), else_=0)).label("query_matches")
            if like_query
            else func.count(models.SitemapEntry.id).label("query_matches"),
        )
        .outerjoin(models.SitemapEntry, models.SitemapEntry.session_id == models.ScanSession.id)
        .filter(models.ScanSession.id.in_(session_ids))
        .group_by(models.ScanSession.id)
        .all()
    )

    rows_by_session_id = {int(row.session_id): row for row in rows}
    result: list[dict[str, int | str]] = []
    for session in sessions:
        row = rows_by_session_id.get(session.id)
        if row is None:
            continue
        result.append(
            {
                "session_id": session.id,
                "sitemap_url": session.sitemap_url,
                "created_at": session.created_at,
                "status": session.status,
                "total_urls": int(row.total_urls or 0),
                "title_done": int(row.title_done or 0),
                "title_errors": int(row.title_errors or 0),
                "test_done": int(row.test_done or 0),
                "test_errors": int(row.test_errors or 0),
                "query_matches": int(row.query_matches or 0),
            }
        )
    return result, total
