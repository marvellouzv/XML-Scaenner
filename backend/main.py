import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from database import Base, engine
from routers.scan import router as scan_router
from routers.sitemap import router as sitemap_router


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Sitemap XML Scanner API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5180",
        "http://127.0.0.1:5180",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("sitemap_entries")}
    with engine.begin() as connection:
        if "scan_error" not in columns:
            connection.execute(text("ALTER TABLE sitemap_entries ADD COLUMN scan_error VARCHAR"))
            logger.info("Added missing column sitemap_entries.scan_error")
        if "source_sitemap" not in columns:
            connection.execute(text("ALTER TABLE sitemap_entries ADD COLUMN source_sitemap VARCHAR"))
            logger.info("Added missing column sitemap_entries.source_sitemap")
        if "test_status" not in columns:
            connection.execute(text("ALTER TABLE sitemap_entries ADD COLUMN test_status VARCHAR DEFAULT 'pending'"))
            logger.info("Added missing column sitemap_entries.test_status")
        if "test_error" not in columns:
            connection.execute(text("ALTER TABLE sitemap_entries ADD COLUMN test_error VARCHAR"))
            logger.info("Added missing column sitemap_entries.test_error")
        if "test_http_status" not in columns:
            connection.execute(text("ALTER TABLE sitemap_entries ADD COLUMN test_http_status INTEGER"))
            logger.info("Added missing column sitemap_entries.test_http_status")
        if "test_response_time_ms" not in columns:
            connection.execute(text("ALTER TABLE sitemap_entries ADD COLUMN test_response_time_ms INTEGER"))
            logger.info("Added missing column sitemap_entries.test_response_time_ms")
    logger.info("Database initialized")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(sitemap_router)
app.include_router(scan_router)
