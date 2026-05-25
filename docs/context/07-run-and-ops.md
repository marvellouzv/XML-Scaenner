# 07. Запуск и эксплуатация

## Локальный запуск (рекомендуемый)

### Backend

Из папки `backend`:

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m ensurepip --upgrade
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8011 --host 127.0.0.1
```

### Frontend

Из папки `frontend`:

```powershell
npm install
$env:VITE_BACKEND_PORT=8011
npm run dev -- --port 5180 --strictPort --host 127.0.0.1
```

## Запуск на свободных портах

В репозитории есть скрипт:

- `scripts/start-local.ps1`

Что делает:

- проверяет кандидаты портов для backend и frontend;
- выбирает свободные порты;
- запускает оба dev-сервера;
- пишет параметры запуска в `start-local.log`.

## Порты и CORS

- типовые dev-порты: backend `8011`/`8000`, frontend `5180`/`5173`;
- CORS в backend явно разрешает `5173` и `5180`;
- при других frontend-портах используйте Vite proxy (`/api`) и `VITE_BACKEND_PORT`.

## Env-переменные backend

Базовые:

- `DATABASE_URL`
- `MAX_CONCURRENT_REQUESTS`
- `REQUEST_DELAY_SECONDS`
- `TITLE_SCAN_MAX_ROUNDS`
- `MAX_SITEMAP_URLS`
- `URL_TEST_MAX_CONCURRENT`
- `URL_TEST_DELAY_SECONDS`
- `URL_TEST_MAX_ROUNDS`
- `URL_TEST_TIMEOUT_SECONDS`

См. шаблон: `backend/.env.example`.

## Docker

Быстрый запуск:

```powershell
docker compose up -d --build
```

См. подробности: `DOCKER.md`.

## Операционные проверки после изменений

Минимальный smoke-check:

1. `GET /health` возвращает 200.
2. Загрузка тестового sitemap проходит до конца.
3. `SCAN TITLES` и `TEST URL` доходят до `done`.
4. `EXPORT` отдает корректный `.xlsx`.
5. Архив показывает и восстанавливает сессии.
