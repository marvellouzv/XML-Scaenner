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
    document_type: str | None
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
URL_TEST_CANCELLED: set[int] = set()


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


def cancel_url_test(session_id: int) -> None:
    with URL_TEST_RUNTIME_LOCK:
        URL_TEST_CANCELLED.add(session_id)


def clear_url_test_cancel(session_id: int) -> None:
    with URL_TEST_RUNTIME_LOCK:
        URL_TEST_CANCELLED.discard(session_id)


def is_url_test_cancelled(session_id: int) -> bool:
    with URL_TEST_RUNTIME_LOCK:
        return session_id in URL_TEST_CANCELLED


def _is_retryable_status(status_code: int) -> bool:
    return status_code in {408, 425, 429, 500, 502, 503, 504}


def _status_error_text(status_code: int, reason: str | None) -> str:
    phrase = reason or "HTTP error"
    return f"HTTP {status_code}: {phrase}"


def _classify_document_type(
    content_type: str | None,
    content_disposition: str | None,
    body_snippet: str | None,
    status_code: int,
) -> str:
    if status_code == 204:
        return "empty"

    ct = (content_type or "").lower()
    cd = (content_disposition or "").lower()
    snippet = (body_snippet or "").strip().lower()

    if "attachment" in cd:
        return "file"

    if "html" in ct:
        if not snippet:
            return "empty"
        if "<html" in snippet or "<!doctype html" in snippet or "<body" in snippet or "<head" in snippet:
            return "html"
        return "unknown"

    if ct.startswith("text/") and ("<" in snippet and ">" in snippet):
        return "html"

    if ct and not ct.startswith("text/"):
        return "file"

    if snippet:
        return "file"

    return "unknown"


async def _request_probe(client: httpx.AsyncClient, url: str) -> tuple[int, float, str]:
    started = time.perf_counter()
    response = await client.head(url, timeout=TEST_TIMEOUT_SECONDS)
    elapsed_ms = (time.perf_counter() - started) * 1000

    status_code = response.status_code
    content_type = response.headers.get("content-type")
    content_disposition = response.headers.get("content-disposition")
    snippet: str | None = None

    if response.status_code in {405, 501}:
        started = time.perf_counter()
        async with client.stream(
            "GET",
            url,
            headers={"Range": "bytes=0-0"},
            timeout=TEST_TIMEOUT_SECONDS,
        ) as fallback_response:
            status_code = fallback_response.status_code
            content_type = fallback_response.headers.get("content-type")
            content_disposition = fallback_response.headers.get("content-disposition")
            chunks: list[str] = []
            async for chunk in fallback_response.aiter_text():
                chunks.append(chunk)
                if sum(len(part) for part in chunks) >= 2048:
                    break
            snippet = "".join(chunks)
        elapsed_ms = (time.perf_counter() - started) * 1000
        document_type = _classify_document_type(content_type, content_disposition, snippet, status_code)
        return status_code, elapsed_ms, document_type

    # For HTML pages we need a tiny body snippet, otherwise HEAD-only checks
    # can mark valid pages as empty.
    if "html" in (content_type or "").lower():
        try:
            started = time.perf_counter()
            async with client.stream(
                "GET",
                url,
                headers={"Range": "bytes=0-2047"},
                timeout=TEST_TIMEOUT_SECONDS,
            ) as preview_response:
                content_type = preview_response.headers.get("content-type") or content_type
                content_disposition = preview_response.headers.get("content-disposition") or content_disposition
                chunks: list[str] = []
                total_chars = 0
                async for chunk in preview_response.aiter_text():
                    chunks.append(chunk)
                    total_chars += len(chunk)
                    if total_chars >= 2048:
                        break
                snippet = "".join(chunks)
            elapsed_ms += (time.perf_counter() - started) * 1000
        except Exception:  # noqa: BLE001
            snippet = None

    document_type = _classify_document_type(content_type, content_disposition, snippet, status_code)
    return status_code, elapsed_ms, document_type


async def _test_entry(client: httpx.AsyncClient, entry_id: int, url: str, delay_seconds: float) -> UrlTestResult:
    try:
        await asyncio.sleep(delay_seconds)
        status_code, elapsed_ms, document_type = await _request_probe(client, url)

        if status_code >= 400:
            # Distinguish between:
            # - HTTP 500 with rendered HTML error page (content-level server error),
            # - transport/access instability where no meaningful page is returned.
            if status_code == 500 and document_type == "html":
                error_message = "HTTP 500: Server error page returned (HTML rendered)"
                retryable = False
            elif status_code == 500:
                error_message = "HTTP 500: Access/connectivity issue (no rendered page)"
                retryable = True
            else:
                error_message = _status_error_text(status_code, None)
                retryable = _is_retryable_status(status_code)
            return UrlTestResult(
                entry_id=entry_id,
                status="pending" if retryable else "error",
                http_status=status_code,
                response_time_ms=int(elapsed_ms),
                document_type=document_type,
                error_message=error_message,
                should_retry=retryable,
            )

        return UrlTestResult(
            entry_id=entry_id,
            status="done",
            http_status=status_code,
            response_time_ms=int(elapsed_ms),
            document_type=document_type,
            error_message=None,
            should_retry=False,
        )
    except httpx.TimeoutException:
        return UrlTestResult(
            entry_id=entry_id,
            status="pending",
            http_status=None,
            response_time_ms=None,
            document_type=None,
            error_message=f"Timeout after {TEST_TIMEOUT_SECONDS:.0f}s",
            should_retry=True,
        )
    except httpx.RequestError as exc:
        return UrlTestResult(
            entry_id=entry_id,
            status="pending",
            http_status=None,
            response_time_ms=None,
            document_type=None,
            error_message=f"Network error: {exc.__class__.__name__}",
            should_retry=True,
        )
    except Exception as exc:  # noqa: BLE001
        return UrlTestResult(
            entry_id=entry_id,
            status="error",
            http_status=None,
            response_time_ms=None,
            document_type=None,
            error_message=f"Unhandled error: {exc.__class__.__name__}",
            should_retry=False,
        )


async def _run_round(
    client: httpx.AsyncClient,
    targets: list[tuple[int, str]],
    concurrency: int,
    delay_seconds: float,
    session_id: int,
) -> list[int]:
    semaphore = asyncio.Semaphore(concurrency)
    retry_ids: list[int] = []

    async def worker(entry_id: int, url: str) -> None:
        if is_url_test_cancelled(session_id):
            return
        async with semaphore:
            if is_url_test_cancelled(session_id):
                return
            result = await _test_entry(client, entry_id=entry_id, url=url, delay_seconds=delay_seconds)
            db: Session = SessionLocal()
            try:
                crud.update_entry_test_result(
                    db,
                    entry_id=result.entry_id,
                    test_status=result.status,
                    test_http_status=result.http_status,
                    test_response_time_ms=result.response_time_ms,
                    test_document_type=result.document_type,
                    test_error=result.error_message,
                )
            finally:
                db.close()

            if result.should_retry:
                retry_ids.append(result.entry_id)

    await asyncio.gather(*(worker(entry_id, url) for entry_id, url in targets), return_exceptions=True)
    return retry_ids


async def run_url_test(session_id: int) -> None:
    clear_url_test_cancel(session_id)
    db: Session = SessionLocal()
    try:
        crud.mark_session_status(db, session_id=session_id, status="testing")
        if not crud.has_test_results(db, session_id=session_id):
            crud.reset_entry_test_statuses(db, session_id=session_id)
        else:
            crud.reset_pending_entry_test_statuses(db, session_id=session_id)
        entries = crud.get_entries_by_session(db, session_id=session_id)
    finally:
        db.close()

    entry_map = {entry.id: entry.url for entry in entries if entry.test_status == "pending"}
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
                if is_url_test_cancelled(session_id):
                    _set_runtime(
                        session_id,
                        phase="paused",
                        message="TEST URL приостановлен пользователем.",
                        decision=f"Осталось {len(pending_ids)} URL. Нажмите RESUME TEST для продолжения.",
                        pending_urls=len(pending_ids),
                    )
                    db = SessionLocal()
                    try:
                        crud.mark_session_status(db, session_id=session_id, status="loaded")
                    finally:
                        db.close()
                    clear_url_test_cancel(session_id)
                    return

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

                retry_ids = await _run_round(
                    client=client,
                    targets=targets,
                    concurrency=current_concurrency,
                    delay_seconds=current_delay,
                    session_id=session_id,
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
                        test_document_type=None,
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
    finally:
        clear_url_test_cancel(session_id)


async def run_url_test_for_entries(session_id: int, entry_ids: list[int]) -> None:
    clear_url_test_cancel(session_id)
    target_entry_ids = set(entry_ids)
    if not target_entry_ids:
        return

    db: Session = SessionLocal()
    try:
        crud.mark_session_status(db, session_id=session_id, status="testing")
        entries = crud.get_entries_by_ids(db, session_id=session_id, entry_ids=list(target_entry_ids))
    finally:
        db.close()

    entry_map = {entry.id: entry.url for entry in entries if entry.id in target_entry_ids}
    pending_ids = list(entry_map.keys())
    if not pending_ids:
        db = SessionLocal()
        try:
            crud.mark_session_status(db, session_id=session_id, status="loaded")
        finally:
            db.close()
        return

    current_concurrency = TEST_MAX_CONCURRENT
    current_delay = TEST_DELAY_SECONDS

    _set_runtime(
        session_id,
        phase="starting",
        message=f"Подготовка RETEST URL. В очереди {len(pending_ids)} URL.",
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
                if is_url_test_cancelled(session_id):
                    _set_runtime(
                        session_id,
                        phase="paused",
                        message="RETEST URL приостановлен пользователем.",
                        decision=f"Осталось {len(pending_ids)} URL. Нажмите RESUME TEST для продолжения.",
                        pending_urls=len(pending_ids),
                    )
                    db = SessionLocal()
                    try:
                        crud.mark_session_status(db, session_id=session_id, status="loaded")
                    finally:
                        db.close()
                    clear_url_test_cancel(session_id)
                    return

                targets = [(entry_id, entry_map[entry_id]) for entry_id in pending_ids]
                _set_runtime(
                    session_id,
                    phase="round_running",
                    message=(
                        f"RETEST URL, раунд {round_number}/{TEST_MAX_ROUNDS}. "
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

                retry_ids = await _run_round(
                    client=client,
                    targets=targets,
                    concurrency=current_concurrency,
                    delay_seconds=current_delay,
                    session_id=session_id,
                )
                pending_ids = [entry_id for entry_id in retry_ids if entry_id in target_entry_ids]

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
                        test_document_type=None,
                        test_error="Max retries exceeded during TEST URL",
                    )
            finally:
                db.close()

        db = SessionLocal()
        try:
            if crud.has_pending_test_entries(db, session_id=session_id):
                crud.mark_session_status(db, session_id=session_id, status="loaded")
            else:
                crud.mark_session_status(db, session_id=session_id, status="done")
        finally:
            db.close()

        _set_runtime(
            session_id,
            phase="done",
            message="RETEST URL завершен.",
            decision="Результаты статусов и времени ответа обновлены для выбранных URL.",
            pending_urls=0,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("URL retest failed for session_id=%s", session_id)
        db = SessionLocal()
        try:
            crud.mark_session_status(db, session_id=session_id, status="loaded")
        finally:
            db.close()
        _set_runtime(
            session_id,
            phase="error",
            message="RETEST URL прерван из-за внутренней ошибки.",
            decision=f"Ошибка: {exc.__class__.__name__}",
        )
    finally:
        clear_url_test_cancel(session_id)


def create_test_task_id(session_id: int) -> str:
    return f"test-{session_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
