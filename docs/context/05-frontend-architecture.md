# 05. Frontend архитектура

## Общий подход

Frontend построен как UI-слой над API backend:

- централизованный store (Zustand) для состояния сессии и процесса;
- запросы и polling через TanStack Query hooks;
- единый API-клиент (`api/client.ts`);
- компонентная структура для отдельных частей пользовательского сценария.

## Слои frontend

### Store (`store/useSitemapStore.ts`)

Хранит:

- идентификаторы (`sessionId`, `loadJobId`);
- список URL;
- текущий статус процесса (`idle/loading/loaded/scanning/testing/done/error`);
- прогресс и текст ошибки;
- счетчик найденных URL при загрузке.

### API-клиент (`api/client.ts`)

- Axios-инстанс с базовым `baseURL=/api`.
- Увеличенные таймауты для долгих операций (load/export/scan).

### Hooks (`hooks/useSitemapQuery.ts`)

Инкапсулируют все сетевые операции:

- загрузка sitemap (start/progress/result);
- запуск scan titles и polling прогресса;
- запуск test URLs и polling прогресса;
- загрузка текущей сессии;
- экспорт;
- архив и восстановление сессии.

### UI-компоненты (`components/*`)

Ключевые:

- `SitemapInput` - ввод URL и запуск загрузки;
- `WorkStatus` - отображение состояния загрузки/обработки;
- `ActionBar` - кнопки SCAN TITLES, TEST URL, COPY, EXPORT;
- `ScanProgress` - прогресс, runtime диагностика, breakdown ошибок;
- `UrlTable` - таблица URL, поиск, сортировка, фильтрация, пагинация;
- `ArchiveModal` - список и восстановление архивных сессий.

## Прокси и порты

- Dev-прокси задается в `vite.config.ts` для `/api`.
- backend target настраивается через `VITE_BACKEND_PORT` (fallback `8011`).
- это позволяет запускать frontend/backend на разных свободных портах без изменения кода компонентов.
