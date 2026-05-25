from datetime import datetime
from typing import Literal

from pydantic import BaseModel, HttpUrl


class SitemapLoadRequest(BaseModel):
    url: HttpUrl


class ScanStartRequest(BaseModel):
    session_id: int


class SitemapUrlBase(BaseModel):
    id: int
    url: str
    lastmod: str | None = None
    changefreq: str | None = None
    priority: str | None = None
    source_sitemap: str | None = None
    title: str | None = None
    scan_status: Literal["pending", "done", "error"] | None = None
    scan_error: str | None = None
    test_status: Literal["pending", "done", "error"] | None = None
    test_error: str | None = None
    test_http_status: int | None = None
    test_response_time_ms: int | None = None

    class Config:
        from_attributes = True


class SitemapLoadResponse(BaseModel):
    session_id: int
    urls: list[SitemapUrlBase]
    total: int


class SitemapLoadStartResponse(BaseModel):
    job_id: str
    status: Literal["started"]


class SitemapLoadProgressResponse(BaseModel):
    job_id: str
    status: Literal["running", "done", "error"]
    found: int
    total: int | None = None
    session_id: int | None = None
    error: str | None = None


class ScanStartResponse(BaseModel):
    task_id: str
    status: Literal["started"]


class ScanProgressResponse(BaseModel):
    total: int
    scanned: int
    errors: int
    error_breakdown: dict[str, int]
    status: Literal["running", "done"]
    runtime_phase: str | None = None
    runtime_message: str | None = None
    runtime_decision: str | None = None
    runtime_round: int | None = None
    runtime_total_rounds: int | None = None
    runtime_concurrency: int | None = None
    runtime_delay: float | None = None
    runtime_pending_urls: int | None = None
    mode: Literal["titles", "test_urls"] = "titles"


class SessionResponse(BaseModel):
    id: int
    sitemap_url: str
    created_at: datetime
    status: str

    class Config:
        from_attributes = True


class ArchiveSessionItem(BaseModel):
    session_id: int
    sitemap_url: str
    created_at: datetime
    status: str
    total_urls: int
    title_done: int
    title_errors: int
    test_done: int
    test_errors: int
    query_matches: int


class ArchiveListResponse(BaseModel):
    items: list[ArchiveSessionItem]
    total: int
