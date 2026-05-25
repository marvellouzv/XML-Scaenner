# Docker Deployment Guide

## What Is Included

- `backend/Dockerfile`: container for FastAPI + SQLAlchemy + SQLite + sitemap/title/url-test services.
- `frontend/Dockerfile`: multi-stage build (Node.js build + Nginx runtime) for React/Vite app.
- `frontend/nginx.conf`: serves frontend and proxies `/api/*` to backend container.
- `docker-compose.yml`: orchestrates backend + frontend and persistent data volume.

## Technology Stack (Containerized)

- Backend:
  - Python 3.13
  - FastAPI
  - SQLAlchemy
  - SQLite (persisted in Docker volume)
  - httpx
  - pandas + openpyxl
- Frontend:
  - Node.js 22 (build stage)
  - React 18 + TypeScript + Vite (build output)
  - Nginx 1.27 (runtime static server + API proxy)

## Quick Start

From project root:

```bash
docker compose up -d --build
```

Open:

- Frontend: `http://localhost:5180`
- Backend health: `http://localhost:8011/health`

## Stop / Start

```bash
docker compose stop
docker compose start
```

## Rebuild After Changes

```bash
docker compose up -d --build
```

## Logs

```bash
docker compose logs -f backend
docker compose logs -f frontend
```

## Data Persistence

SQLite DB is stored in named Docker volume:

- Volume name: `sitemap_scanner_data`
- Container path: `/app/data/sitemap_scanner.db`

This means data survives container recreation.

## Main Runtime Variables

Configured in `docker-compose.yml`:

- `DATABASE_URL`
- `MAX_CONCURRENT_REQUESTS`
- `REQUEST_DELAY_SECONDS`
- `TITLE_SCAN_MAX_ROUNDS`
- `MAX_SITEMAP_URLS`
- `URL_TEST_MAX_CONCURRENT`
- `URL_TEST_DELAY_SECONDS`
- `URL_TEST_MAX_ROUNDS`
- `URL_TEST_TIMEOUT_SECONDS`

Adjust values in `docker-compose.yml`, then rebuild.
