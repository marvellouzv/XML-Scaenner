# AGENT.md

## Именование файлов и компонентов

- React-компоненты: `PascalCase` (`SitemapInput.tsx`, `UrlTable.tsx`).
- Хуки: `camelCase` с префиксом `use` (`useSitemapQuery.ts`).
- Сторы Zustand: `useXxxStore.ts`.
- Backend-модули: `snake_case.py`.
- Роутеры FastAPI размещать в `backend/routers`.
- Бизнес-логику размещать в `backend/services`.

## Стиль кода

- Frontend:
  - TypeScript `strict` обязателен.
  - ESLint обязателен (`npm run lint`).
  - Prettier обязателен (`npm run format`).
  - Запрещено использовать `any`.
- Backend:
  - Следовать Black-совместимому стилю (PEP8, 88 символов).
  - Явные типы в публичных функциях.
  - Логирование через модуль `logging`.

## Как добавлять новый endpoint (backend)

1. Добавить/обновить Pydantic-схемы в `backend/schemas.py`.
2. Добавить CRUD-операции в `backend/crud.py` при необходимости.
3. Добавить бизнес-логику в `backend/services/*`.
4. Добавить endpoint в соответствующий роутер (`backend/routers/*.py`).
5. Подключить роутер в `backend/main.py`, если новый файл роутера.
6. Обновить `README.md` и `HANDOFF.md`.

## Как добавлять новый компонент (frontend)

1. Создать компонент в `frontend/src/components`.
2. Добавить типы в `frontend/src/types/index.ts` при необходимости.
3. Интегрировать API-запросы через `frontend/src/hooks/useSitemapQuery.ts`.
4. Состояние сессии/данных хранить в Zustand (`frontend/src/store/useSitemapStore.ts`).
5. Не делать прямые HTTP вызовы внутри случайных компонентов: только через `api/client.ts` + hooks.
6. Обновить `README.md` и `HANDOFF.md`.

## Миграции Alembic

- Инициализировать/применять из папки `backend`:
  - `alembic revision -m "description"`
  - `alembic upgrade head`
  - `alembic downgrade -1`
- Все изменения SQLAlchemy-моделей должны сопровождаться новой миграцией.

## Запрещённые паттерны

- `any` в TypeScript.
- Прямые SQL-запросы в обход SQLAlchemy ORM.
- Хардкод URL backend в компонентах (использовать `api/client.ts` и Vite proxy).
- Блокирующие сетевые операции в FastAPI endpoint без async-обёртки.
- Необработанные исключения в API-слое.

## Документация и handoff

- При заметных изменениях кода, API, схемы данных, UX или процессов обязательно обновлять `HANDOFF.md`.
- При изменениях архитектуры/процессов/правил работы обновлять `AGENT.md`.
- Поддерживать модульную документацию контекста в `docs/context/*` в актуальном состоянии.
- Для онбординга использовать `docs/context/README.md` как точку входа.

