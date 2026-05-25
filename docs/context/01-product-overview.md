# 01. Обзор продукта и структуры

## Назначение

`Sitemap XML Scanner` - веб-приложение для SEO-анализа sitemap:

- загрузка `sitemap.xml` по URL;
- рекурсивный обход `sitemapindex`, включая `.xml.gz`;
- просмотр и фильтрация списка URL;
- асинхронное сканирование `<title>`;
- безопасная проверка ответа URL (TEST URL);
- экспорт результатов в Excel.

## Технологический стек

- Backend: FastAPI, SQLAlchemy, Alembic, SQLite, httpx.
- Frontend: React, TypeScript, Vite, Tailwind, Zustand, TanStack Query.
- Инфраструктура: Docker Compose (опционально), локальный PowerShell-скрипт запуска.

## Структура репозитория

- `backend/` - API, ORM, сервисы, миграции.
- `frontend/` - интерфейс, клиент API, UI-компоненты.
- `scripts/` - вспомогательные скрипты запуска.
- `docs/context/` - модульная документация по функциям.
- `README.md` - общее описание проекта.
- `AGENT.md` - правила разработки и сопровождения.
- `HANDOFF.md` - журнал изменений и текущего состояния.

## Ключевые функциональные зоны

1. Загрузка sitemap:
   - фоновая загрузка job-пайплайном (`/load/start` -> `/load/progress` -> `/load/result`);
   - поддержка `urlset`, `sitemapindex`, gzip.
2. Работа с таблицей URL:
   - поиск, сортировка, фильтрация по source sitemap, пагинация.
3. SCAN TITLES:
   - многорундовый async-скан с ретраями и адаптивным троттлингом.
4. TEST URL:
   - HEAD, затем fallback GET с `Range: bytes=0-0`.
5. Архив сессий:
   - просмотр, поиск, восстановление ранее сохраненных сессий.
6. Экспорт:
   - `.xlsx` с базовым форматированием.
