[2026-04-22] - Inicializaciya i realizaciya polnoj versii Sitemap XML Scanner

Chto bylo sdelano
- Sozdana polnaya struktura proekta backend/frontend.
- Realizovan backend na FastAPI:
  - SQLAlchemy modeli `ScanSession` i `SitemapEntry`.
  - CRUD-sloj dlya sessij, URL i progressa skanirovaniya.
  - Servis rekursivnogo parsinga sitemap (`urlset` + `sitemapindex`).
  - Servis asinhronnogo skanirovaniya title s `asyncio.Semaphore`, timeout i User-Agent.
  - Routy: zagruzka sitemap, eksport Excel, zapusk skanirovaniya, progress, poluchenie sessii.
  - Eksport v Excel cherez pandas/openpyxl (bold zagolovki, avto shirina kolonok).
  - Nastroeny CORS, healthcheck, logging.
- Dobavlen Alembic:
  - `alembic.ini`, `env.py`, `script.py.mako`.
  - Pervaya migraciya `20260422_0001_init.py`.
- Realizovan frontend na React + TypeScript:
  - Zustand store dlya `sessionId`, `urls`, `status`, `progress`.
  - API-sloj i hooks na TanStack Query.
  - Komponenty: `SitemapInput`, `ActionBar`, `ScanProgress`, `UrlTable`.
  - Funkcii COPY/EXPORT/SCAN TITLES, polling progressa, obnovlenie tablicy posle skanirovaniya.
  - Sortirovka, filtr, paginaciya, podsveka oshibok, ikonki statusov.
  - Temizaciya Light/Dark, bazovye animacii Framer Motion.
  - Nastroeny Tailwind, ESLint, Prettier, Vite proxy.
- Dobavleny i zapolneny `README.md` i `AGENT.md`.

Kakie fajly izmeneny
- Backend:
  - `backend/main.py`
  - `backend/database.py`
  - `backend/models.py`
  - `backend/schemas.py`
  - `backend/crud.py`
  - `backend/requirements.txt`
  - `backend/.env.example`
  - `backend/routers/sitemap.py`
  - `backend/routers/scan.py`
  - `backend/routers/__init__.py`
  - `backend/services/sitemap_parser.py`
  - `backend/services/title_scanner.py`
  - `backend/services/__init__.py`
  - `backend/alembic.ini`
  - `backend/alembic/env.py`
  - `backend/alembic/script.py.mako`
  - `backend/alembic/versions/20260422_0001_init.py`
- Frontend:
  - `frontend/package.json`
  - `frontend/tsconfig.json`
  - `frontend/vite.config.ts`
  - `frontend/tailwind.config.ts`
  - `frontend/postcss.config.js`
  - `frontend/eslint.config.js`
  - `frontend/.prettierrc`
  - `frontend/index.html`
  - `frontend/src/main.tsx`
  - `frontend/src/App.tsx`
  - `frontend/src/index.css`
  - `frontend/src/types/index.ts`
  - `frontend/src/api/client.ts`
  - `frontend/src/hooks/useSitemapQuery.ts`
  - `frontend/src/store/useSitemapStore.ts`
  - `frontend/src/components/SitemapInput.tsx`
  - `frontend/src/components/UrlTable.tsx`
  - `frontend/src/components/ActionBar.tsx`
  - `frontend/src/components/ScanProgress.tsx`
  - `frontend/src/components/ui/button.tsx`
  - `frontend/src/components/ui/input.tsx`
  - `frontend/src/components/ui/card.tsx`
  - `frontend/src/components/ui/skeleton.tsx`
  - `frontend/src/components/ui/select.tsx`
  - `frontend/src/components/ui/progress.tsx`
  - `frontend/src/components/ui/toast.tsx`
  - `frontend/src/lib/utils.ts`
- Root:
  - `README.md`
  - `AGENT.md`
  - `HANDOFF.md`

Izvestnye problemy / TODO
- Nužno ustanovit zavisimosti i zapustit proverki lokalno (`pip install`, `npm install`, `npm run build`), v etom shage ne vypolnyalos.

[2026-04-22] - Utochnenie logiki skanirovaniya title

Chto bylo sdelano
- Dobavlena zaderzhka `0.5` sek pered kazhdym HTTP-zaprosom v title scanner.
- Parametr vynesen v konfiguraciyu `REQUEST_DELAY_SECONDS` (po umolchaniyu `0.5`).
- Podtverzhdena logika zapuska skana tolko po knopke `SCAN TITLES` (avto-zapuska net).

Kakie fajly izmeneny
- `backend/services/title_scanner.py`
- `backend/.env.example`
- `README.md`
- `HANDOFF.md`

Izvestnye problemy / TODO
- Nužno ustanovit zavisimosti i zapustit proverki lokalno (`pip install`, `npm install`, `npm run build`), v etom shage ne vypolnyalos.

[2026-04-22] - Utochnenie obrabotki oshibok sitemap (403) i teksta oshibok v UI

Chto bylo sdelano
- V parser sitemap dobavleny HTTP-zagolovki (`User-Agent`, `Accept`, `Accept-Language`) dlya luchshej sovmestimosti s celovymi saytami.
- Dobavlena yavnaya obrabotka `403 Forbidden` s ponyatnym tekstom oshibki backend.
- Frontend teper pokazyvaet `detail` iz backend oshibki vmesto obshchego `Request failed with status code 400`.

Kakie fajly izmeneny
- `backend/services/sitemap_parser.py`
- `frontend/src/hooks/useSitemapQuery.ts`
- `HANDOFF.md`

Izvestnye problemy / TODO
- Nužno ustanovit zavisimosti i zapustit proverki lokalno (`pip install`, `npm install`, `npm run build`), v etom shage ne vypolnyalos.

[2026-04-22] - Ubrana kolonka Priority iz UI-tablicy

Chto bylo sdelano
- Iz `UrlTable` udaleny kolonka `Priority`, ee yachejki i sortirovka po `priority`.
- Tablica ostalas s kolonkamy: `#`, `URL`, `Last Modified`, `Title` (pri skanirovanii).

Kakie fajly izmeneny
- `frontend/src/components/UrlTable.tsx`
- `HANDOFF.md`

Izvestnye problemy / TODO
- Nužno ustanovit zavisimosti i zapustit proverki lokalno (`pip install`, `npm install`, `npm run build`), v etom shage ne vypolnyalos.

[2026-04-22] - Rasshireny varianty paginacii v tablice URL

Chto bylo sdelano
- V selector kolichestva strok na stranicu dobavleny znacheniya `500`, `1000`, `5000`.

Kakie fajly izmeneny
- `frontend/src/components/UrlTable.tsx`
- `HANDOFF.md`

Izvestnye problemy / TODO
- Nužno ustanovit zavisimosti i zapustit proverki lokalno (`pip install`, `npm install`, `npm run build`), v etom shage ne vypolnyalos.

[2026-04-22] - Adaptivnoe snizhenie skorosti skana i detalizaciya oshibok

Chto bylo sdelano
- V model SitemapEntry dobavleno pole scan_error dlya teksta oshibki po konkretnomu URL.
- Title scanner peredelan na mnogoraundovyj re-scan:
  - oshibki seti/timeout/5xx/429 schitayutsya vremennymi i uhodjat na pereobhod;
  - pri nalichii oshibok snizhaetsya skorost (menshe concurrency, bolshe delay);
  - posle ischerpaniya raundov element poluchaet error s prichinoj.
- Dobavlena migraciya 20260422_0002_add_scan_error.py.
- V main.py dobavlena startup-sovmestimost: esli kolonki scan_error net v staroj BD, ona dobavlyaetsya avtomaticheski.
- UI-tablica teper pokazyvaet tekst oshibki v kolonke Title i tooltip s detalami ot servera.

Kakie fajly izmeneny
- ackend/models.py
- ackend/schemas.py
- ackend/crud.py
- ackend/services/title_scanner.py
- ackend/main.py
- ackend/alembic/versions/20260422_0002_add_scan_error.py
- rontend/src/types/index.ts
- rontend/src/components/UrlTable.tsx
- README.md
- HANDOFF.md

Izvestnye problemy / TODO
- Nuzhno ustanovit zavisimosti i zapustit proverki lokalno (pip install, 
pm install, 
pm run build), v etom shage ne vypolnyalos.

[2026-04-22] - Tooltip s razbivkoj tipov oshibok v poloske oshibok

Chto bylo sdelano
- GET /api/scan/progress teper vozvraschaet error_breakdown (slovar tip oshibki -> kolichestvo).
- V UI progress dobavlena poloska oshibok; pri navedenii na krasnyj segment pokazyvaetsya, skolko kakih oshibok.

Kakie fajly izmeneny
- ackend/schemas.py
- ackend/crud.py
- ackend/routers/scan.py
- rontend/src/types/index.ts
- rontend/src/store/useSitemapStore.ts
- rontend/src/App.tsx
- rontend/src/components/ScanProgress.tsx
- HANDOFF.md

Izvestnye problemy / TODO
- Nuzhno ustanovit zavisimosti i zapustit proverki lokalno (pip install, 
pm install, 
pm run build), v etom shage ne vypolnyalos.

[2026-04-22] - Uvelichen timeout klientskih API-zaprosov

Chto bylo sdelano
- Uvelichen bazovyj timeout axios do 120000ms.
- Dlya POST /api/sitemap/load i GET /api/sitemap/export ustanovlen timeout 300000ms.

Kakie fajly izmeneny
- rontend/src/api/client.ts
- HANDOFF.md

Izvestnye problemy / TODO
- Nuzhno ustanovit zavisimosti i zapustit proverki lokalno (pip install, 
pm install, 
pm run build), v etom shage ne vypolnyalos.

[2026-04-22] - Stabilizaciya timeout vo vremya SCAN TITLES

Chto bylo sdelano
- Uvelicheny timeouty dlya scan-endpointov: POST /api/scan/titles i GET /api/scan/progress do 60000ms.
- Dlya polling progress dobavlen retry (5 popytok) s exponentalnoj zaderzhkoj.
- Ubran globalnyj error-banner na edinichnyh timeout polling, chtoby aktivnoe skanirovanie ne sryvalos vizualno.

Kakie fajly izmeneny
- rontend/src/api/client.ts
- rontend/src/hooks/useSitemapQuery.ts
- rontend/src/App.tsx
- HANDOFF.md

Izvestnye problemy / TODO
- Nuzhno ustanovit zavisimosti i zapustit proverki lokalno (pip install, 
pm install, 
pm run build), v etom shage ne vypolnyalos.

[2026-04-22] - Dobavleno okno statusa raboty

Chto bylo sdelano
- Dobavlen otdelnyj blok statusa v UI, chtoby bylo srazu vidno:
  - skolko URL najdeno;
  - tekuschij status processa;
  - skolko URL uzhe obrabotano.
- Blok vyveden na glavnyj ekran srazu pod polem LOAD.

Kakie fajly izmeneny
- rontend/src/components/WorkStatus.tsx
- rontend/src/App.tsx
- HANDOFF.md

Izvestnye problemy / TODO
- Nuzhno ustanovit zavisimosti i zapustit proverki lokalno (pip install, 
pm install, 
pm run build), v etom shage ne vypolnyalos.

[2026-04-22] - Realtime uvelichenie schetchika najdennyh URL vo vremya LOAD

Chto bylo sdelano
- Dobavlen fonovyj pipeline zagruzki sitemap:
  - POST /api/sitemap/load/start
  - GET /api/sitemap/load/progress
  - GET /api/sitemap/load/result
- V parser dobavlen callback progress, chtoby backend otdaval tekuschij ound po mere nahozhdeniya URL.
- Frontend pereveden na novu� loading-shemu s polling kazhduyu sekundu.
- V okne statusa "Naydeno URL" teper rastet v realnom vremeni pri status=loading.

Kakie fajly izmeneny
- ackend/services/sitemap_parser.py
- ackend/schemas.py
- ackend/routers/sitemap.py
- rontend/src/types/index.ts
- rontend/src/api/client.ts
- rontend/src/store/useSitemapStore.ts
- rontend/src/hooks/useSitemapQuery.ts
- rontend/src/App.tsx
- README.md
- HANDOFF.md

Izvestnye problemy / TODO
- Nuzhno ustanovit zavisimosti i zapustit proverki lokalno (pip install, 
pm install, 
pm run build), v etom shage ne vypolnyalos.

[2026-04-22] - Uskorennoe obnovlenie schetchika najdennyh URL pri LOAD

Chto bylo sdelano
- Backend progress-callback teper obnovlyaetsya na kazhdyj novyj URL (a ne raz v 20 URL).
- Frontend polling load/progress uskor�� do 300ms dlya bolee gladkogo rosta schetchika.

Kakie fajly izmeneny
- ackend/services/sitemap_parser.py
- rontend/src/hooks/useSitemapQuery.ts
- HANDOFF.md

Izvestnye problemy / TODO
- Nuzhno ustanovit zavisimosti i zapustit proverki lokalno (pip install, 
pm install, 
pm run build), v etom shage ne vypolnyalos.

[2026-04-22] - Plavnaya animaciya schetchika najdennyh URL

Chto bylo sdelano
- V WorkStatus dobavlena animaciya schetchika "Naydeno URL".
- Teper dazhe pri ochen bystrom finishe backend chislo rastet vizualno po shag�� vmesto momentalnogo skachka.

Kakie fajly izmeneny
- rontend/src/components/WorkStatus.tsx
- HANDOFF.md

Izvestnye problemy / TODO
- Nuzhno ustanovit zavisimosti i zapustit proverki lokalno (pip install, 
pm install, 
pm run build), v etom shage ne vypolnyalos.

[2026-04-22] - Fiks domena www v rezultatakh

Chto bylo sdelano
- Pri LOAD sitemap dobavlena normalizaciya hosta: esli sitemap URL zagruzhen s www., to URL togo zhe domena bez www privodyatsya k www.
- Primeneno kak dlya fonovogo pipeline (/load/start), tak i dlya sinkhronnogo (/load).

Kakie fajly izmeneny
- ackend/routers/sitemap.py
- HANDOFF.md

Izvestnye problemy / TODO
- Nuzhno ustanovit zavisimosti i zapustit proverki lokalno (pip install, 
pm install, 
pm run build), v etom shage ne vypolnyalos.

[2026-04-22] - Rasshirennyj runtime-status skanera title (chto delaet i kakie resheniya prinimaet)

Chto bylo sdelano
- V title scanner dobavlen runtime-state po sessii:
  - tekuschaya faza (starting, 
ound_running, decision, inalizing, done, error),
  - tekst tekuschego dejstviya,
  - tekst prinyatogo resheniya,
  - tekuschij round, parallelizm, zaderzhka, ochered URL.
- GET /api/scan/progress rasshiren etimi polyami.
- Frontend progress-panel teper pokazyvaet blok "Status skanera" i "Reshenie", chtoby videt, skaniruet li on ili zamedlyaetsya/pereobhodit.

Kakie fajly izmeneny
- ackend/services/title_scanner.py
- ackend/routers/scan.py
- ackend/schemas.py
- rontend/src/types/index.ts
- rontend/src/store/useSitemapStore.ts
- rontend/src/App.tsx
- rontend/src/components/ScanProgress.tsx
- HANDOFF.md

Izvestnye problemy / TODO
- Nuzhno ustanovit zavisimosti i zapustit proverki lokalno (pip install, 
pm install, 
pm run build), v etom shage ne vypolnyalos.

[2026-04-22] - Diagnosticheskiy status title-scan + recovery zavisshih sessij

Chto bylo sdelano
- Progress endpoint skanera title rasshiren runtime-polyami:
  - faza (
untime_phase),
  - tekuschee dejstvie (
untime_message),
  - prinyatoe reshenie (
untime_decision),
  - round, parallelizm, zaderzhka, ochered URL.
- V UI progress dobavlen blok, gde vidno chto skaner delaet i pochemu menyaet skorost.
- Dobavlen recovery dlya sessij, zastravshih v scanning posle restarta servera:
  - pending URL pometchayutsya kak error s prichinoj,
  - sessiya zakryvaetsya, chtoby ne visela beskonechno.

Kakie fajly izmeneny
- ackend/services/title_scanner.py
- ackend/routers/scan.py
- ackend/schemas.py
- ackend/crud.py
- rontend/src/types/index.ts
- rontend/src/store/useSitemapStore.ts
- rontend/src/App.tsx
- rontend/src/components/ScanProgress.tsx
- HANDOFF.md

Izvestnye problemy / TODO
- Nuzhno ustanovit zavisimosti i zapustit proverki lokalno (pip install, 
pm install, 
pm run build), v etom shage ne vypolnyalos.

[2026-04-23] - Podderzhka sitemapindex s ukazaniem istochnika URL + vyrovneny porty zapuska

Chto bylo sdelano
- Dopolnen backend dlya atribucii istochnika kazhdogo URL:
  - v parser sitemap pri razbore `urlset` zapisivaetsya `source_sitemap` (URL tekuschego sitemap-fajla),
  - pole `source_sitemap` dobavleno v model `SitemapEntry`, Pydantic-shemy i bulk-save v CRUD.
- Dobavlena migraciya Alembic `20260423_0003_add_source_sitemap.py`.
- Dobavlena startup-sovmestimost v `main.py`: esli kolonki `source_sitemap` net v staroj SQLite, ona dobavlyaetsya avtomaticheski.
- V Excel eksport dobavlena kolonka `Source Sitemap`.
- Frontend:
  - v tip `SitemapUrl` dobavleno pole `source_sitemap`,
  - v `UrlTable` dobavlena kolonka `Sitemap File` (sortiruemaya),
  - v yachejke pokazyvaetsya imya sitemap-fajla, polnyj URL dostupen v tooltip.
- Ispravleny oshibki TypeScript v `SitemapInput`/`UrlTable`.
- Vyrovnen konfig zapuska:
  - `frontend/vite.config.ts` port izmenen na `5180`, proxy ostalsya na backend `8011`,
  - backend CORS rasshiren dlya `localhost/127.0.0.1` na portah `5173` i `5180`.

Kakie fajly izmeneny
- `backend/models.py`
- `backend/schemas.py`
- `backend/crud.py`
- `backend/main.py`
- `backend/routers/sitemap.py`
- `backend/alembic/versions/20260423_0003_add_source_sitemap.py`
- `frontend/src/types/index.ts`
- `frontend/src/components/UrlTable.tsx`
- `frontend/src/components/SitemapInput.tsx`
- `frontend/vite.config.ts`
- `README.md`
- `HANDOFF.md`

Izvestnye problemy / TODO
- `python -m compileall backend` v etom okruzhenii padal na WinError 5 (zapis v `__pycache__`), no na rabotosposobnost API eto ne vliyaet.
- `alembic` CLI v lokalnom venv ne najden kak ispolnyaemyj skript; rekomenduetsya ustanovit/pereustanovit zavisimosti backend (`pip install -r requirements.txt`) i progonit `alembic upgrade head`.

[2026-04-23] - Fiks obrabotki sitemapindex: normalizaciya `www` dlya dochernih sitemap

Chto bylo sdelano
- V parser dobavlena normalizaciya hosta dochernih sitemap (`sitemapindex -> sitemap/loc`):
  - esli kornevoj sitemap zagruzhen s `www.`, a dochernij `loc` sсыlaetsya na tot zhe domen bez `www`, host avtomaticheski privoditsya k `www`.
- Eto ustranyaet padeniya pri obhode index-fajlov na sajtah, gde bez `www` vozvrashchayutsya oshibki dostupnosti.
- Live-proverka na `https://www.scp-garant.ru/sitemap.xml`:
  - job zavershilsya so status `done`,
  - naydeno `33739` URL,
  - v API rezultatakh prisutstvuet `source_sitemap` (napr. `https://www.scp-garant.ru/sitemap-iblock-17.xml`).

Kakie fajly izmeneny
- `backend/services/sitemap_parser.py`
- `HANDOFF.md`

Izvestnye problemy / TODO
- Для запуска backend на 8011 используется системный Python (`python -m uvicorn`), потому что в локальном `backend/venv` отсутствует `uvicorn`.

[2026-04-23] - Dobavlen otdelnyj UI-filtr po Sitemap File

Chto bylo sdelano
- V `UrlTable` dobavlen otdelnyj select-filtr `Sitemap File` dlya bystrogo vydeleniya URL iz konkretnogo docherniego sitemap.
- Spisok variantov filtra formiruetsya dinamicheski iz `source_sitemap` tekuschego nabora dannyh.
- Filtr rabotaet sovmestno s poiskiem po URL, sortirovkoy i paginaciey.
- Pri vyborе filtra stranicа sbрасывается na 1.

Kakie fajly izmeneny
- `frontend/src/components/UrlTable.tsx`
- `HANDOFF.md`

Izvestnye problemy / TODO
- Net.

[2026-04-23] - Podderzhka sitemap v gzip-arhivah (.xml.gz)

Chto bylo sdelano
- V backend parser dobavlena podderzhka gzip sitemap (`.xml.gz`):
  - zagruzka kontenta kak bytes,
  - opredelenie gzip po URL, zagolovkam i magic bytes,
  - raspakovka pered XML-analizom,
  - zashchita na sluchaj, kogda server otdaet uzhe raspakovannyj XML.
- Dobavlena bolee ponyatnaya oshibka pri neudachnoj raspakovke gzip.
- V frontend-validaciyu URL dobavlena yavnaia podderzhka `.xml.gz`.

Kakie fajly izmeneny
- `backend/services/sitemap_parser.py`
- `frontend/src/components/SitemapInput.tsx`
- `README.md`
- `HANDOFF.md`

Izvestnye problemy / TODO
- Net.

[2026-04-23] - Dobavlena favicon-ikonka v XML stile

Chto bylo sdelano
- Sozdana novaia favicon `frontend/public/favicon.svg` v XML-tematike.
- Ikonka podklyuchena v `frontend/index.html` cherez `<link rel="icon" ...>`.

Kakie fajly izmeneny
- `frontend/public/favicon.svg`
- `frontend/index.html`
- `HANDOFF.md`

Izvestnye problemy / TODO
- Net.

[2026-04-23] - Ubran zhestkij limit 50000 URL pri load sitemap

Chto bylo sdelano
- V parser `parse_sitemap` ubrano zhestkoe ogranichenie 50000 po umolchaniyu.
- Dobavlen konfiguriruemyj limit cherez peremennuyu `MAX_SITEMAP_URLS`:
  - `0` ili pustoe znachenie = bez limita,
  - polozhitelnoe chislo = limitirovat obrabotku.
- Routery `POST /api/sitemap/load` i fonovyj `load/start` teper peredayut limit iz `.env`.
- Obnovleny `backend/.env.example` i `README.md`.

Kakie fajly izmeneny
- `backend/services/sitemap_parser.py`
- `backend/routers/sitemap.py`
- `backend/.env.example`
- `README.md`
- `HANDOFF.md`

Izvestnye problemy / TODO
- Pri ochen bolshih sitemap vyrastet nagruzka na RAM, tak kak URL sobirayutsya v pamyati do zapisi v BD.

[2026-04-29] - Dobavlena knopka TEST URL i bezopasnaya proverka otklika servera

Chto bylo sdelano
- Backend:
  - Dobavlen novyj servis `backend/services/url_tester.py` dlya proverki URL bez skachivaniya polnoj stranicy:
    - snaсhala `HEAD`,
    - fallback `GET` s `Range: bytes=0-0` dlya serverov bez HEAD.
  - Dobavleny endpointy:
    - `POST /api/scan/test-urls`
    - `GET /api/scan/test-progress?session_id=...`
  - Dobavleny polya v `SitemapEntry`:
    - `test_status`, `test_error`, `test_http_status`, `test_response_time_ms`.
  - Dobavlen CRUD dlya sbrosa/obnovleniya URL-test statusov i progressa.
  - Dobavlena startup-sovmestimost kolonnok v `main.py` i migraciya Alembic:
    - `20260429_0004_add_url_test_fields.py`.
- Frontend:
  - V `ActionBar` dobavlena knopka `TEST URL`.
  - Dobavleny API/hook dlya starta i polling progressa URL testa.
  - V `UrlTable` dobavlena kolonka `URL Test` (HTTP code, response time, tekst oshibki).
  - `ScanProgress` sdelan universalnym dlya `SCAN TITLES` i `TEST URL`.
  - `WorkStatus` dopolnen statusom `testing`.
- Konfiguraciya:
  - Dobavleny peremennye v `.env.example`:
    - `URL_TEST_MAX_CONCURRENT`, `URL_TEST_DELAY_SECONDS`, `URL_TEST_MAX_ROUNDS`, `URL_TEST_TIMEOUT_SECONDS`.

Kakie fajly izmeneny
- `backend/models.py`
- `backend/schemas.py`
- `backend/crud.py`
- `backend/main.py`
- `backend/routers/scan.py`
- `backend/services/url_tester.py` (new)
- `backend/alembic/versions/20260429_0004_add_url_test_fields.py` (new)
- `backend/.env.example`
- `frontend/src/types/index.ts`
- `frontend/src/api/client.ts`
- `frontend/src/hooks/useSitemapQuery.ts`
- `frontend/src/components/ActionBar.tsx`
- `frontend/src/components/UrlTable.tsx`
- `frontend/src/components/ScanProgress.tsx`
- `frontend/src/components/WorkStatus.tsx`
- `frontend/src/App.tsx`
- `README.md`
- `HANDOFF.md`

Izvestnye problemy / TODO
- При очень больших sitemap итоговая загрузка все еще зависит от объема RAM (список URL пока собирается в памяти перед bulk insert).

[2026-04-29] - Arhiv sesij skanirovaniya s vosstanovleniem

Chto bylo sdelano
- Backend:
  - Dobavlen endpoint spiska arhiva: `GET /api/sitemap/archive` (query, limit, offset).
  - Dobavlen endpoint vosstanovleniya sesii: `GET /api/sitemap/archive/{session_id}`.
  - V arhive otdayutsya kratkie metriky po sessii:
    - total_urls,
    - title_done/title_errors,
    - test_done/test_errors,
    - query_matches po poisikovomu URL-zaprosu.
  - Dopolneny schema-modeli dlya arhiva v `schemas.py`.
  - Dopolnen CRUD agregatami po sessiyam v `get_archive_sessions`.
- Frontend:
  - Dobavlena knopka `Архив` v shapkе ryadom s pereklyuchatelem Light/Dark.
  - Sozdan modal `ArchiveModal`:
    - spisok sesij so vremenem, saytом i svodkoy,
    - poisik po URL,
    - knopka `Восстановить` dlya zagruzki sesii v tablicu.
  - Dobavleny tipy i API-client metody dlya arhiva.
  - Dobavleny hooks `useArchiveQuery` i `useRestoreArchiveMutation`.

Kakie fajly izmeneny
- `backend/schemas.py`
- `backend/crud.py`
- `backend/routers/sitemap.py`
- `frontend/src/types/index.ts`
- `frontend/src/api/client.ts`
- `frontend/src/hooks/useSitemapQuery.ts`
- `frontend/src/components/ArchiveModal.tsx` (new)
- `frontend/src/App.tsx`
- `README.md`
- `HANDOFF.md`

Izvestnye problemy / TODO
- Pri bolshom kolichestve sessij arhiv vyvoditsya postranichno server-side (limit=100 v UI), no bez knopok pagination v modalkе (pokazyvaetsya pervaya porciya).

[2026-04-30] - Dobavlena docker-infrastruktura dlya bystrogo razvorota

Chto bylo sdelano
- Sozdan `backend/Dockerfile` (Python 3.13 + FastAPI stack).
- Sozdan `frontend/Dockerfile` (multi-stage build: Node build + Nginx runtime).
- Sozdan `frontend/nginx.conf` dlya razdachi React-build i proxy `/api` v backend.
- Sozdan `docker-compose.yml` dlya zapuska backend+frontend odnoj komandoj.
- Dobavlen named volume `sitemap_scanner_data` dlya persistenta SQLite.
- Dobavleny `.dockerignore` dlya backend i frontend.
- Sozdan `DOCKER.md` s opisaniem tekhnologij, arhitektury i komand razvorota.
- V README dobavlena ssylka na Docker-gajd.

Kakie fajly izmeneny
- `backend/Dockerfile` (new)
- `backend/.dockerignore` (new)
- `frontend/Dockerfile` (new)
- `frontend/nginx.conf` (new)
- `frontend/.dockerignore` (new)
- `docker-compose.yml` (new)
- `DOCKER.md` (new)
- `README.md`
- `HANDOFF.md`

Izvestnye problemy / TODO
- Dlya realnogo produkcionnogo razvorota rekomenduetsya dobavit TLS/reverse-proxy (naprimer Caddy/Nginx na hoste).

[2026-05-19] - Lokalnyj zapusk na svobodnyh portah + dinamicheskij Vite proxy

## Summary of Changes
- `frontend/vite.config.ts`: proxy target beretsya iz `VITE_BACKEND_PORT` (fallback `8011`), chtoby frontend i backend mogli startovat na raznyh svobodnyh portah.
- `scripts/start-local.ps1`: skript podbora svobodnyh portov i zapuska oboih servisov.
- `start-local.log`: poslednie ispolzuemye URL/porty pri lokalnom zapuske.

## Files Changed
- `frontend/vite.config.ts`
- `scripts/start-local.ps1` (new)
- `start-local.log` (generated)
- `HANDOFF.md`

## Risks / Known Issues
- Porty `8000` i `5173` mogut byt zanyaty drugimi processami ? skript/vruchnuyu vybrat sleduyushchie svobodnye.
- CORS v `backend/main.py` razreshen tolko dlya `5173` i `5180`; pri frontend na drugom porte API rabotaet cherez Vite proxy (`/api`), pryamye zaprosy na backend iz brauzera mogut trebovat dopolneniya CORS.

## Validation Performed
- Backend `8011`: `/health` 200, `/docs` 200.
- Frontend `5180`: `/` 200, `VITE_BACKEND_PORT=8011`.

## Next Steps
- Pri neobhodimosti rasshirit CORS dlya dopolnitelnyh dev-portov.
- Obnovit README s primerom: `$env:VITE_BACKEND_PORT=8011; npm run dev -- --port 5180`.

[2026-05-25] - Modularnaya dokumentaciya konteksta v otdelnoj papke

## Summary of Changes
- Sozdana otdelnaya papka `docs/context` s razdeleniem dokumentacii po funkcionalnym blokam dlya poetapnogo onbordinga.
- Dobavleny 7 tematicheskih dokumentov: product overview, backend API, backend services, data model, frontend architecture, user workflows, run/ops.
- V `README.md` dobavlena tochka vhoda v novuyu modulnuyu dokumentaciyu.
- V `AGENT.md` zakrepleno trebovanie podderzhivat `docs/context/*` v aktualnom sostoyanii.

## Files Changed
- `docs/context/README.md` (new)
- `docs/context/01-product-overview.md` (new)
- `docs/context/02-backend-api.md` (new)
- `docs/context/03-backend-services.md` (new)
- `docs/context/04-data-model.md` (new)
- `docs/context/05-frontend-architecture.md` (new)
- `docs/context/06-user-workflows.md` (new)
- `docs/context/07-run-and-ops.md` (new)
- `README.md`
- `AGENT.md`
- `HANDOFF.md`

## Risks / Known Issues
- Chast dokumentacii v repo vedetsya v translite; novye razdely tozhe oformleny v etom stile dlya konsistentnosti.
- Pri dobavlenii novyh endpointov/komponentov nuzhno obnovlyat sootvetstvuyushchie sekcii v `docs/context`, inache vozniknet raskhozhdenie mezhdu kodom i docs.

## Validation Performed
- Proverena nalichie papki `docs/context` i vseh indeksnyh failov.
- Provereno, chto `README.md` i `AGENT.md` sсыlayutsya na novuyu strukturu dokumentacii.

## Next Steps
- Pri sleduyuschem izmenenii API dobavit primery request/response v `docs/context/02-backend-api.md`.
- Pri sleduyuschem izmenenii UI dobavit screenshot-based primer scenariev v `docs/context/06-user-workflows.md`.

[2026-05-25] - Fiks pereklyucheniya Light/Dark temi v UI

## Summary of Changes
- Ustranena prichina, iz-za kotoroj knopka Light/Dark meniala sostoyanie, no vizualno tema pochti ne menyalas: osnovnye komponenty byli zhardko privyazany k temnym `zinc-*` klassam.
- Vnedrena theme-aware stilizaciya cherez uzhe sushchestvuyushchie CSS peremennye i Tailwind tokeny (`background`, `foreground`, `card`, `muted`, `muted-foreground`, `border`) v bazovyh UI-komponentah i klyuchevyh ekranah.
- V `App` dobavlen adaptivnyj fon dlya svetloj i temnoj temi (chernovoj gradient dlya dark + svetlyj gradient dlya light), chtoby pereklyuchenie bylo vizualno odnoznachnym.

## Files Changed
- `frontend/src/index.css`
- `frontend/tailwind.config.ts`
- `frontend/src/App.tsx`
- `frontend/src/components/UrlTable.tsx`
- `frontend/src/components/ArchiveModal.tsx`
- `frontend/src/components/WorkStatus.tsx`
- `frontend/src/components/ScanProgress.tsx`
- `frontend/src/components/ui/button.tsx`
- `frontend/src/components/ui/card.tsx`
- `frontend/src/components/ui/input.tsx`
- `frontend/src/components/ui/select.tsx`
- `frontend/src/components/ui/progress.tsx`
- `frontend/src/components/ui/skeleton.tsx`
- `frontend/src/components/ui/toast.tsx`
- `HANDOFF.md`

## Risks / Known Issues
- Chast cvetov vse eshche ostayetsya semanticheski nejtralnoj (`blue` dlya ssylok/progress), eto norm dlya tekuschej UX-konvencii, no mozhno dopolnitelno tonko vyrovnyat kontrast pod brand-guidelines.
- Esli v budushchem dobavyatsya novye komponenty s `zinc-*`, pereklyuchenie temi snova mozhet vygljadet nepolnym; rekomenduetsya ispolzovat tokeny temi po umolchaniyu.

## Validation Performed
- `frontend`: `npm run build` uspeshen (TypeScript + Vite build bez oshibok).
- Provereny lint-diagnostiki po izmenennym frontend failam: oshibok ne obnaruzheno.
- Proverena logika pereklyucheniya: klass `dark` ostalsya na `documentElement`, i teper osnovnye vidimye blokи deystvitelno pereklyuchayutsya mezhdu dark/light.

## Next Steps
- Progonyat ruchnoj UI-scenarij: neskolko raz pereklyuchit Light/Dark na glavnom ekrane i v Archive modal, proverit chtoby kontrast teksta/tablits ostavalsya komfortnym.
- Pri neobhodimosti vynesti gradienty shell-fona v otdelnye utility-klassy/Tailwind layer dlya bolee prostoj podderzhki dizajna.