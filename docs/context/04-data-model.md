# 04. Модель данных

## Технология хранения

- Основная БД: SQLite.
- ORM: SQLAlchemy.
- Миграции: Alembic.
- В `database.py` включен режим WAL для лучшей конкурентной записи.

## Сущность `scan_sessions`

Назначение: хранение сессий обработки sitemap.

Основные поля:

- `id` - PK.
- `sitemap_url` - исходный URL sitemap.
- `created_at` - дата/время создания.
- `status` - состояние сессии (`loaded`, `scanning`, `done`).

## Сущность `sitemap_entries`

Назначение: хранение URL и результатов обработки.

Основные поля:

- `id` - PK.
- `session_id` - FK на `scan_sessions.id`.
- `url` - URL страницы.
- `lastmod`, `changefreq`, `priority` - данные из sitemap.
- `source_sitemap` - источник URL внутри sitemapindex.
- `title` - найденный `<title>`.
- `scan_status`, `scan_error` - статус и причина ошибки title scan.
- `test_status`, `test_error` - статус и ошибка URL test.
- `test_http_status` - HTTP код при тестировании URL.
- `test_response_time_ms` - время ответа URL.

## Эволюция схемы (по миграциям)

- базовые таблицы и связи;
- добавление `scan_error`;
- добавление `source_sitemap`;
- добавление полей `test_*`.

## Особенности согласованности

- часть runtime-состояния (например, прогресс активной операции) хранится in-memory в API-слое и не является частью постоянной модели БД;
- backend содержит startup-проверки структуры таблиц и при необходимости добавляет недостающие колонки.
