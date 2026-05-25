# 02. Backend API

Документ описывает публичные endpoint-ы backend (`backend/routers`), их назначение и типовые сценарии использования.

## Системный endpoint

- `GET /health`
  - Назначение: healthcheck API.
  - Ответ: `{ "status": "ok" }`.

## Группа `/api/sitemap`

### Загрузка sitemap

- `POST /api/sitemap/load/start`
  - Стартует фоновую загрузку sitemap.
  - Возвращает `job_id`.

- `GET /api/sitemap/load/progress?job_id=...`
  - Возвращает статус job загрузки и число уже найденных URL.
  - Используется frontend polling для realtime-индикатора.

- `GET /api/sitemap/load/result?job_id=...`
  - Возвращает итоговые URL после завершения job.

- `POST /api/sitemap/load`
  - Синхронная загрузка sitemap (legacy/упрощенный режим).

### Работа с сессиями и экспортом

- `GET /api/sitemap/session?session_id={id}`
  - Возвращает URL текущей сессии сканирования.

- `GET /api/sitemap/export?session_id={id}`
  - Генерирует и возвращает Excel-файл `.xlsx`.

### Архив

- `GET /api/sitemap/archive?query=...&limit=...&offset=...`
  - Список сохраненных сессий с агрегированными метриками.

- `GET /api/sitemap/archive/{session_id}`
  - Восстановление выбранной архивной сессии в рабочее состояние UI.

## Группа `/api/scan`

### Сканирование title

- `POST /api/scan/titles`
  - Запуск асинхронного сканирования `<title>` для URL текущей сессии.

- `GET /api/scan/progress?session_id={id}`
  - Прогресс сканирования title.
  - Содержит процент, счетчики, runtime-состояние и breakdown ошибок.

### Проверка URL

- `POST /api/scan/test-urls`
  - Запуск безопасного тестирования доступности URL.

- `GET /api/scan/test-progress?session_id={id}`
  - Прогресс URL-тестирования (по структуре близок к progress title).

## Примечания по API-поведениям

- Прогресс загрузки sitemap (`load/*`) хранится в памяти процесса (in-memory jobs).
- После рестарта backend runtime прогресс-структуры могут быть сброшены; в коде есть логика recovery состояния сканирования.
- Для фронтенда используется Vite proxy (`/api`), чтобы минимизировать CORS-проблемы в dev.
