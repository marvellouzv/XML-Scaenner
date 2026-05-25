# Sitemap XML Scanner

Веб-приложение для загрузки `sitemap.xml`, рекурсивного обхода `sitemapindex`, просмотра URL-структуры, асинхронного сканирования `<title>` страниц и экспорта в Excel.

## Возможности

- Загрузка sitemap по URL через FastAPI + `httpx` (таймаут 10 сек).
- Поддержка `urlset` и `sitemapindex` с рекурсивным обходом.
- Сохранение сессий и URL в SQLite через SQLAlchemy.
- Асинхронное сканирование title с ограничением конкурентности (по умолчанию 5).
- Прогресс сканирования с polling каждые 2 секунды.
- Экспорт результата в `.xlsx` (жирные заголовки, автоширина).
- UI на React + TypeScript + Tailwind + Zustand + TanStack Query.

## Структура

```text
sitemap-scanner/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── crud.py
│   ├── routers/
│   │   ├── sitemap.py
│   │   └── scan.py
│   ├── services/
│   │   ├── sitemap_parser.py
│   │   └── title_scanner.py
│   ├── alembic/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.ts
├── README.md
├── AGENT.md
└── HANDOFF.md
```

## Backend: установка и запуск

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8011
```

## Frontend: установка и запуск

```bash
cd frontend
npm install
npm run dev
```

Приложение будет доступно на `http://localhost:5180`.

## Переменные окружения

Создайте `backend/.env`:

```env
DATABASE_URL=sqlite:///./sitemap_scanner.db
MAX_CONCURRENT_REQUESTS=5
REQUEST_DELAY_SECONDS=0.5
TITLE_SCAN_MAX_ROUNDS=3
MAX_SITEMAP_URLS=0
```

## API

- `POST /api/sitemap/load` — загрузка sitemap.
- `GET /api/sitemap/export?session_id={id}` — экспорт в `.xlsx`.
- `GET /api/sitemap/session?session_id={id}` — получить URL текущей сессии.
- `POST /api/scan/titles` — запуск сканирования title.
- `GET /api/scan/progress?session_id={id}` — прогресс сканирования.

## Примечания

- CORS настроен для `localhost:5173` и `localhost:5180`.
- Для больших sitemap действует лимит 50 000 URL на одну загрузку.
- Frontend собран в strict TypeScript режиме.

## Realtime progress pri LOAD sitemap

Teper zagruzka sitemap mozet idti v fonovom zadanii:
- POST /api/sitemap/load/start -> { job_id, status }
- GET /api/sitemap/load/progress?job_id=... -> tekuschij status i ound (kolichestvo uzhe najdennyh URL)
- GET /api/sitemap/load/result?job_id=... -> finalnyj spisok URL posle zaversheniya

Frontend ispolzuet etot polling, poetomu v okne statusa schetchik "Naydeno URL" rastet vo vremya parsinga.

## Limit URL v sitemap

- Parametr `MAX_SITEMAP_URLS` upravlyaet maksimalnym kolichestvom URL pri zagruzke sitemap.
- `MAX_SITEMAP_URLS=0` (po umolchaniyu) oznachaet "bez limita".
- Uкажите polozhitelnoe chislo, esli nuzhno iskusstvenno ogranichit obrabotku (naprimer `200000`).

## Podderzhka sitemap v arhivah (.xml.gz)

Parser podderzhivaet sitemap-fajly v gzip-arhivah (`.xml.gz`).
- Esli URL/otvet opredelyaetsya kak gzip, backend avtomaticheski raspakovyvaet soderzhimoe i analiziraet XML.
- Rabotaet kak dlya odinochnogo sitemap, tak i dlya `sitemapindex`, gde dochernie `loc` mogut ssylatsya na `.xml.gz`.

## TEST URL (server response check without full page download)

Added a new safe URL probing mode:
- Button: `TEST URL`
- Start endpoint: `POST /api/scan/test-urls`
- Progress endpoint: `GET /api/scan/test-progress?session_id={id}`

How it works:
- First tries `HEAD` request.
- If `HEAD` is not supported (`405`/`501`), uses fallback `GET` with `Range: bytes=0-0`.
- Saves for each URL:
  - `test_status` (`pending|done|error`)
  - `test_http_status`
  - `test_response_time_ms`
  - `test_error`

Load safety defaults (configurable in `backend/.env`):
- `URL_TEST_MAX_CONCURRENT=3`
- `URL_TEST_DELAY_SECONDS=0.3`
- `URL_TEST_MAX_ROUNDS=3`
- `URL_TEST_TIMEOUT_SECONDS=5`

Adaptive throttling:
- On temporary errors/timeouts the scanner retries in next rounds,
- reduces concurrency and increases delay to avoid overloading target website.

## Archive sessions and restore

- Header button `Архив` opens a modal with saved scan sessions.
- The archive list contains:
  - scan date/time,
  - site/sitemap URL,
  - short scan summary (URLs, title/test success/errors),
  - URL match count for search query.
- Search field filters archive sessions by URL (`/api/sitemap/archive?query=...`).
- You can restore any archived session back into the main table (`/api/sitemap/archive/{session_id}`).

## Docker

- Dlya bystrogo razvorota smotrite [DOCKER.md](./DOCKER.md).
- One-command start:
  - `docker compose up -d --build`

## Dokumentaciya po kontekstu (modulno)

Detalinaya dokumentaciya po funkcionalnym blokam raznesena v papku:

- `docs/context/README.md`

Razdely pozvolyayut izuchat proekt chastyami: product overview, backend API, servisy, model dannyh, frontend arhitektura, user workflows i run/ops.
