import asyncio
import logging
import math
import os
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime

import httpx
from sqlalchemy.orm import Session

import crud
from database import SessionLocal


logger = logging.getLogger(__name__)
TEST_MAX_CONCURRENT = int(os.getenv("URL_TEST_MAX_CONCURRENT", "3"))
TEST_DELAY_SECONDS = float(os.getenv("URL_TEST_DELAY_SECONDS", "0.3"))
TEST_MAX_ROUNDS = int(os.getenv("URL_TEST_MAX_ROUNDS", "3"))
TEST_TIMEOUT_SECONDS = float(os.getenv("URL_TEST_TIMEOUT_SECONDS", "5"))


@dataclass
class UrlTestResult:
    entry_id: int
    status: str
    http_status: int | None
    response_time_ms: int | None
    error_message: str | None
    should_retry: bool


@dataclass
class UrlTestRuntimeState:
    phase: str
    message: str
    decision: str | None
    round: int
    total_rounds: int
    current_concurrency: int
    current_delay: float
    pending_urls: int
    updated_at: str


URL_TEST_RUNTIME: dict[int, UrlTestRuntimeState] = {}
URL_TEST_RUNTIME_LOCK = threading.Lock()


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _set_runtime(session_id: int, **kwargs) -> None:
    with URL_TEST_RUNTIME_LOCK:
        current = URL_TEST_RUNTIME.get(session_id)
        if current is None:
            current = UrlTestRuntimeState(
                phase="idle",
                message="Ожидание запуска проверки URL.",
                decision=None,
                round=0,
                total_rounds=TEST_MAX_ROUNDS,
                current_concurrency=TEST_MAX_CONCURRENT,
                current_delay=TEST_DELAY_SECONDS,
                pending_urls=0,
                updated_at=_now_iso(),
            )
        for key, value in kwargs.items():
            setattr(current, key, value)
        current.updated_at = _now_iso()
        URL_TEST_RUNTIME[session_id] = current


def get_url_test_runtime(session_id: int) -> dict[str, str | int | float | None] | None:
    with URL_TEST_RUNTIME_LOCK:
        state = URL_TEST_RUNTIME.get(session_id)
        return asdict(state) if state else None


def _is_retryable_status(status_code: int) -> bool:
    return status_code in {408, 425, 429, 500, 502, 503, 504}


def _status_error_text(status_code: int, reason: str | None) -> str:
    phrase = reason or "HTTP error"
    return f"HTTP {status_code}: {phrase}"


async def _request_probe(client: httpx.AsyncClient, url: str) -> tuple[int, float]:
    started = time.perf_counter()
    response = await client.head(url, timeout=TEST_TIMEOUT_SECONDS)
    elapsed_ms = (time.perf_counter() - started) * 1000

    if response.status_code in {405, 501}:
        started = time.perf_counter()
        async with client.stream(
            "GET",
            url,
            headers={"Range": "bytes=0-0"},
            timeout=TEST_TIMEOUT_SECONDS,
        ) as fallback_response:
            status_code = fallback_response.status_code
        elapsed_ms = (time.perf_counter() - started) * 1000
        return status_code, elapsed_ms

    return response.status_code, elapsed_ms


async def _test_entry(client: httpx.AsyncClient, entry_id: int, url: str, delay_seconds: float) -> UrlTestResult:
    try:
        await asyncio.sleep(delay_seconds)
        status_code, elapsed_ms = await _request_probe(client, url)

        if status_code >= 400:
            error_message = _status_error_text(status_code, None)
            retryable = _is_retryable_status(status_code)
            return UrlTestResult(
                entry_id=entry_id,
                status="pending" if retryable else "error",
                http_status=status_code,
                response_time_ms=int(elapsed_ms),
                error_message=error_message,
                should_retry=retryable,
            )

        return UrlTestResult(
            entry_id=entry_id,
            status="done",
            http_status=status_code,
            response_time_ms=int(elapsed_ms),
            error_message=None,
            should_retry=False,
        )
    except httpx.TimeoutException:
        return UrlTestResult(
            entry_id=entry_id,
            status="pending",
            http_status=None,
            response_time_ms=None,
            error_message=f"Timeout after {TEST_TIMEOUT_SECONDS:.0f}s",
            should_retry=True,
        )
    except httpx.RequestError as exc:
        return UrlTestResult(
            entry_id=entry_id,
            status="pending",
            http_status=None,
            response_time_ms=None,
            error_message=f"Network error: {exc.__class__.__name__}",
            should_retry=True,
        )
    except Exception as exc:  # noqa: BLE001
        return UrlTestResult(
            entry_id=entry_id,
            status="error",
            http_status=None,
            response_time_ms=None,
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
            result = await _test_entry(client, entry_id=entry_id, url=url, delay_seconds=delay_seconds)
            db: Session = SessionLocal()
            try:
                crud.update_entry_test_result(
                    db,
                    entry_id=result.entry_id,
                    test_status=result.status,
                    test_http_status=result.http_status,
                    test_response_time_ms=result.response_time_ms,
                    test_error=result.error_message,
                )
            finally:
                db.close()

            if result.should_retry:
                retry_ids.append(result.entry_id)

    await asyncio.gather(*(worker(entry_id, url) for entry_id, url in targets), return_exceptions=True)
    return retry_ids


async def run_url_test(session_id: int) -> None:
    db: Session = SessionLocal()
    try:
        crud.mark_session_status(db, session_id=session_id, status="testing")
        crud.reset_entry_test_statuses(db, session_id=session_id)
        entries = crud.get_entries_by_session(db, session_id=session_id)
    finally:
        db.close()

    entry_map = {entry.id: entry.url for entry in entries}
    pending_ids = list(entry_map.keys())
    current_concurrency = TEST_MAX_CONCURRENT
    current_delay = TEST_DELAY_SECONDS

    _set_runtime(
        session_id,
        phase="starting",
        message=f"Подготовка TEST URL. В очереди {len(pending_ids)} URL.",
        decision=None,
        round=0,
        total_rounds=TEST_MAX_ROUNDS,
        current_concurrency=current_concurrency,
        current_delay=current_delay,
        pending_urls=len(pending_ids),
    )

    headers = {"User-Agent": "Mozilla/5.0 (compatible; SitemapScanner/1.0)"}

    try:
        async with httpx.AsyncClient(follow_redirects=True, headers=headers) as client:
            for round_number in range(1, TEST_MAX_ROUNDS + 1):
                if not pending_ids:
                    break

                targets = [(entry_id, entry_map[entry_id]) for entry_id in pending_ids]
                _set_runtime(
                    session_id,
                    phase="round_running",
                    message=(
                        f"Проверяю TEST URL, раунд {round_number}/{TEST_MAX_ROUNDS}. "
                        f"В очереди {len(targets)} URL. Пауза перед запросом {current_delay:.2f}с."
                    ),
                    decision=(
                        f"Параллелизм: {current_concurrency}. "
                        "При росте ошибок автоматически замедлюсь, чтобы снизить нагрузку на сайт."
                    ),
                    round=round_number,
                    current_concurrency=current_concurrency,
                    current_delay=current_delay,
                    pending_urls=len(targets),
                )

                retry_ids = await _run_round(client=client, targets=targets, concurrency=current_concurrency, delay_seconds=current_delay)
                pending_ids = retry_ids

                if pending_ids:
                    next_concurrency = max(1, math.floor(current_concurrency / 2))
                    next_delay = min(3.0, current_delay * 1.5)
                    _set_runtime(
                        session_id,
                        phase="decision",
                        message=f"Раунд {round_number} завершен. На переобход отправлено {len(pending_ids)} URL.",
                        decision=(
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

        if pending_ids:
            db = SessionLocal()
            try:
                for entry_id in pending_ids:
                    crud.update_entry_test_result(
                        db,
                        entry_id=entry_id,
                        test_status="error",
                        test_http_status=None,
                        test_response_time_ms=None,
                        test_error="Max retries exceeded during TEST URL",
                    )
            finally:
                db.close()

        db = SessionLocal()
        try:
            crud.mark_session_status(db, session_id=session_id, status="done")
        finally:
            db.close()

        _set_runtime(
            session_id,
            phase="done",
            message="TEST URL завершен.",
            decision="Результаты статусов и времени ответа сохранены.",
            pending_urls=0,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("URL test failed for session_id=%s", session_id)
        db = SessionLocal()
        try:
            crud.mark_session_status(db, session_id=session_id, status="done")
        finally:
            db.close()
        _set_runtime(
            session_id,
            phase="error",
            message="TEST URL прерван из-за внутренней ошибки.",
            decision=f"Ошибка: {exc.__class__.__name__}",
        )


def create_test_task_id(session_id: int) -> str:
    return f"test-{session_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
