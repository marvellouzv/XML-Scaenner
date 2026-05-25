import asyncio
import logging
import math
import os
import re
import threading
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime

import httpx
from sqlalchemy.orm import Session

import crud
from database import SessionLocal


logger = logging.getLogger(__name__)
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
REQUEST_DELAY_SECONDS = float(os.getenv("REQUEST_DELAY_SECONDS", "0.5"))
MAX_SCAN_ROUNDS = int(os.getenv("TITLE_SCAN_MAX_ROUNDS", "3"))
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


@dataclass
class ScanResult:
    entry_id: int
    title: str | None
    status: str
    error_message: str | None
    should_retry: bool


@dataclass
class ScanRuntimeState:
    phase: str
    message: str
    decision: str | None
    round: int
    total_rounds: int
    current_concurrency: int
    current_delay: float
    pending_urls: int
    updated_at: str


SCAN_RUNTIME: dict[int, ScanRuntimeState] = {}
SCAN_RUNTIME_LOCK = threading.Lock()


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _set_runtime(session_id: int, **kwargs) -> None:
    with SCAN_RUNTIME_LOCK:
        current = SCAN_RUNTIME.get(session_id)
        if current is None:
            current = ScanRuntimeState(
                phase="idle",
                message="Ожидание запуска",
                decision=None,
                round=0,
                total_rounds=MAX_SCAN_ROUNDS,
                current_concurrency=MAX_CONCURRENT_REQUESTS,
                current_delay=REQUEST_DELAY_SECONDS,
                pending_urls=0,
                updated_at=_now_iso(),
            )
        for key, value in kwargs.items():
            setattr(current, key, value)
        current.updated_at = _now_iso()
        SCAN_RUNTIME[session_id] = current


def get_scan_runtime(session_id: int) -> dict[str, str | int | float | None] | None:
    with SCAN_RUNTIME_LOCK:
        state = SCAN_RUNTIME.get(session_id)
        return asdict(state) if state else None


def _extract_title(html: str) -> str | None:
    match = TITLE_RE.search(html)
    if not match:
        return None
    title = re.sub(r"\s+", " ", match.group(1)).strip()
    return title or None


def _format_status_error(response: httpx.Response) -> str:
    status = response.status_code
    reason = response.reason_phrase or "HTTP error"
    return f"HTTP {status}: {reason}"


def _is_retryable_status(status_code: int) -> bool:
    return status_code in {408, 425, 429, 500, 502, 503, 504}


async def _scan_entry(client: httpx.AsyncClient, entry_id: int, url: str, delay_seconds: float) -> ScanResult:
    try:
        await asyncio.sleep(delay_seconds)
        response = await client.get(url, timeout=8.0)
        if response.status_code >= 400:
            error_message = _format_status_error(response)
            return ScanResult(
                entry_id=entry_id,
                title=None,
                status="pending" if _is_retryable_status(response.status_code) else "error",
                error_message=error_message,
                should_retry=_is_retryable_status(response.status_code),
            )

        return ScanResult(
            entry_id=entry_id,
            title=_extract_title(response.text),
            status="done",
            error_message=None,
            should_retry=False,
        )
    except httpx.TimeoutException:
        return ScanResult(entry_id=entry_id, title=None, status="pending", error_message="Timeout after 8s", should_retry=True)
    except httpx.RequestError as exc:
        return ScanResult(
            entry_id=entry_id,
            title=None,
            status="pending",
            error_message=f"Network error: {exc.__class__.__name__}",
            should_retry=True,
        )
    except Exception as exc:  # noqa: BLE001
        return ScanResult(
            entry_id=entry_id,
            title=None,
            status="error",
            error_message=f"Unhandled error: {exc.__class__.__name__}",
            should_retry=False,
        )


async def _run_round(
    client: httpx.AsyncClient,
    targets: list[tuple[int, str]],
    concurrency: int,
    delay_seconds: float,
) -> list[int]:
    semaphore = asyncio.Semaphore(concurrency)
    retry_ids: list[int] = []

    async def worker(entry_id: int, url: str) -> None:
        async with semaphore:
            result = await _scan_entry(client, entry_id=entry_id, url=url, delay_seconds=delay_seconds)
            db: Session = SessionLocal()
            try:
                crud.update_entry_title(
                    db,
                    entry_id=result.entry_id,
                    title=result.title,
                    scan_status=result.status,
                    scan_error=result.error_message,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to persist scan result for entry_id=%s: %s", entry_id, exc)
            finally:
                db.close()

            if result.should_retry:
                retry_ids.append(result.entry_id)

    await asyncio.gather(*(worker(entry_id, url) for entry_id, url in targets), return_exceptions=True)
    return retry_ids


async def run_title_scan(session_id: int) -> None:
    db: Session = SessionLocal()
    try:
        crud.mark_session_status(db, session_id=session_id, status="scanning")
        crud.reset_entry_scan_statuses(db, session_id=session_id)
        entries = crud.get_entries_by_session(db, session_id=session_id)
    finally:
        db.close()

    entry_map = {entry.id: entry.url for entry in entries}
    pending_ids = list(entry_map.keys())
    current_concurrency = MAX_CONCURRENT_REQUESTS
    current_delay = REQUEST_DELAY_SECONDS

    _set_runtime(
        session_id,
        phase="starting",
        message=f"Подготовка сканирования. В очереди {len(pending_ids)} URL.",
        decision=None,
        round=0,
        total_rounds=MAX_SCAN_ROUNDS,
        current_concurrency=current_concurrency,
        current_delay=current_delay,
        pending_urls=len(pending_ids),
    )

    headers = {"User-Agent": "Mozilla/5.0 (compatible; SitemapScanner/1.0)"}

    try:
        async with httpx.AsyncClient(follow_redirects=True, headers=headers) as client:
            for round_number in range(1, MAX_SCAN_ROUNDS + 1):
                if not pending_ids:
                    break

                targets = [(entry_id, entry_map[entry_id]) for entry_id in pending_ids]
                _set_runtime(
                    session_id,
                    phase="round_running",
                    message=(
                        f"Сканирую раунд {round_number}/{MAX_SCAN_ROUNDS}. "
                        f"В очереди {len(targets)} URL. Пауза перед запросом {current_delay:.2f}с."
                    ),
                    decision=(
                        f"Параллелизм: {current_concurrency}. "
                        f"Если ошибок станет много, уменьшу скорость и отправлю URL на переобход."
                    ),
                    round=round_number,
                    current_concurrency=current_concurrency,
                    current_delay=current_delay,
                    pending_urls=len(targets),
                )

                retry_ids = await _run_round(
                    client=client,
                    targets=targets,
                    concurrency=current_concurrency,
                    delay_seconds=current_delay,
                )

                error_ratio = (len(retry_ids) / len(targets)) if targets else 0.0
                logger.info(
                    "Title scan round %s: targets=%s, retry=%s, error_ratio=%.2f, concurrency=%s, delay=%.2f",
                    round_number,
                    len(targets),
                    len(retry_ids),
                    error_ratio,
                    current_concurrency,
                    current_delay,
                )

                pending_ids = retry_ids
                if pending_ids:
                    next_concurrency = max(1, math.floor(current_concurrency / 2))
                    next_delay = min(3.0, current_delay * 1.5)
                    _set_runtime(
                        session_id,
                        phase="decision",
                        message=f"Раунд {round_number} завершен. На переобход отправлено {len(pending_ids)} URL.",
                        decision=(
                            f"Обнаружены ошибки/таймауты. "
                            f"Снижаю параллелизм {current_concurrency}→{next_concurrency}, "
                            f"увеличиваю паузу {current_delay:.2f}с→{next_delay:.2f}с."
                        ),
                        round=round_number,
                        current_concurrency=next_concurrency,
                        current_delay=next_delay,
                        pending_urls=len(pending_ids),
                    )
                    current_concurrency = next_concurrency
                    current_delay = next_delay
                else:
                    _set_runtime(
                        session_id,
                        phase="decision",
                        message=f"Раунд {round_number} завершен без повторных URL.",
                        decision="Ошибок почти нет, продолжаю без замедления.",
                        round=round_number,
                        current_concurrency=current_concurrency,
                        current_delay=current_delay,
                        pending_urls=0,
                    )

        if pending_ids:
            db = SessionLocal()
            try:
                for entry_id in pending_ids:
                    crud.update_entry_title(
                        db,
                        entry_id=entry_id,
                        title=None,
                        scan_status="error",
                        scan_error="Max retries exceeded during re-scan",
                    )
            finally:
                db.close()

            _set_runtime(
                session_id,
                phase="finalizing",
                message=f"Часть URL не удалось обработать после {MAX_SCAN_ROUNDS} раундов.",
                decision=f"Пометил {len(pending_ids)} URL как error (исчерпаны переобходы).",
                pending_urls=len(pending_ids),
            )

        db = SessionLocal()
        try:
            crud.mark_session_status(db, session_id=session_id, status="done")
        finally:
            db.close()

        _set_runtime(
            session_id,
            phase="done",
            message="Сканирование завершено.",
            decision="Финальные результаты сохранены в базе.",
            pending_urls=0,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Title scan failed for session_id=%s", session_id)
        db = SessionLocal()
        try:
            crud.mark_session_status(db, session_id=session_id, status="done")
        finally:
            db.close()
        _set_runtime(
            session_id,
            phase="error",
            message="Сканирование прервано из-за внутренней ошибки.",
            decision=f"Ошибка: {exc.__class__.__name__}",
        )


def create_task_id(session_id: int) -> str:
    return f"{session_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"

