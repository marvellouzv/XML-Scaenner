from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class ScanSession(Base):
    __tablename__ = "scan_sessions"

    id = Column(Integer, primary_key=True, index=True)
    sitemap_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String, default="loaded", nullable=False)  # loaded | scanning | done
    urls = relationship("SitemapEntry", back_populates="session", cascade="all, delete-orphan")


class SitemapEntry(Base):
    __tablename__ = "sitemap_entries"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("scan_sessions.id"), nullable=False, index=True)
    url = Column(String, nullable=False, index=True)
    lastmod = Column(String, nullable=True)
    changefreq = Column(String, nullable=True)
    priority = Column(String, nullable=True)
    source_sitemap = Column(String, nullable=True)
    title = Column(String, nullable=True)
    scan_status = Column(String, default="pending", nullable=False)  # pending | done | error
    scan_error = Column(String, nullable=True)
    test_status = Column(String, default="pending", nullable=False)  # pending | done | error
    test_error = Column(String, nullable=True)
    test_http_status = Column(Integer, nullable=True)
    test_response_time_ms = Column(Integer, nullable=True)

    session = relationship("ScanSession", back_populates="urls")
