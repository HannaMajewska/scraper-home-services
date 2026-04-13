# Local Business Directory Scraper for USA Home Services

Сбор публичных карточек локального бизнеса с Yellow Pages по категории и городу (США): постраничный обход, нормализация данных, дедупликация, экспорт **CSV** / **Excel** и **веб-панель** для запуска задач и работы с результатами.

---

## Ценность для бизнеса

- **Ускоряет сбор рыночных данных** — вместо ручного копирования контактов из каталога вы получаете структурированную таблицу за один прогон.
- **Снижает операционные затраты** — одна команда или клик в панели заменяет часы рутины для отделов продаж, маркетинга и аналитики.
- **Даёт воспроизводимый процесс** — параметры поиска (ключевое слово, город, число страниц) фиксируются; результаты и артефакты прогона лежат в папке run.
- **Поддерживает дальнейшую обработку** — единый формат строк (название, сайт, телефон, категория, адрес, город, URL источника) удобно отдавать в CRM, обогащение или отчёты.

## Какие проблемы решает сервис

| Проблема | Как помогает решение |
|----------|----------------------|
| Нет единого списка компаний по нише и гео | Парсинг выдачи Yellow Pages с заданным ключом и городом |
| Дубли и «грязные» поля вручную | Нормализация записей и дедупликация перед экспортом |
| Нужны и «разовый скрипт», и удобный UI | CLI для автоматизации + дашборд для операторов |
| Блокировки и нестабильные страницы | Playwright (Chromium); при блокировке отдельных страниц прогон продолжается |
| Нужны Excel и отбор строк | Экспорт XLSX; в панели — фильтры, сортировка, удаление выбранных строк из прогона |

## Цели продукта

1. **Надёжно** доставать карточки бизнеса из открытого каталога в допустимых условиях использования сайта.
2. **Предсказуемо** отдавать данные в табличном виде для бизнес-процессов.
3. **Удобно** сопровождать цикл «запуск → мониторинг → выгрузка → правка списка» через веб-интерфейс без обязательного знания CLI.

---

## Интерфейс веб-панели: обзор

После запуска `uvicorn` откройте **http://127.0.0.1:8000/** . Интерфейс состоит из вкладок **Run** (текущий прогон и таблица результатов) и **Results history** (недавние запуски).

Ниже — места для скриншотов. Положите файлы в каталог **`docs/screenshots/`** (его можно создать вручную) и при необходимости поправьте имена в ссылках.

### Общий вид: шапка и навигация

*Скриншот: логотип/заголовок, вкладки Run и Results history.*

![Шапка и вкладки](docs/screenshots/ui-01-header-tabs.png)

### Вкладка Run — запуск задачи

*Скриншот: поле CLI-команды, кнопки старта, опции CSV/XLSX.*

![Форма запуска scrape](docs/screenshots/ui-02-run-form.png)

### Вкладка Run — сводка по прогону

*Скриншот: блок Run summary (keyword, city, статус, счётчики страниц и записей).*

![Сводка по прогону](docs/screenshots/ui-03-run-summary.png)

### Вкладка Run — таблица Results

*Скриншот: таблица с колонками компании, сайта, телефона, категории и т.д.; чекбоксы слева; сортировка по Company name и Category.*

![Таблица результатов](docs/screenshots/ui-04-results-table.png)

### Фильтры и элементы управления

*Скриншот: поиск по названию, фильтры по городу и категории, кастомный список **Any website** (как у выпадающего UI), **Rows per page** в том же визуальном стиле, кнопка Apply filters.*

![Фильтры и переключатель строк на странице](docs/screenshots/ui-05-filters-per-page.png)

### Массовые действия в Results

*Скриншот: панель с текстом «N rows selected», кнопки **Select all** и **Delete selected** (появляется при отмеченных строках).*

![Массовые действия в таблице Results](docs/screenshots/ui-06-results-bulk-actions.png)

### Пагинация и выгрузки

*Скриншот: блок пагинации и ссылки Download CSV / Download Excel.*

![Пагинация и выгрузки](docs/screenshots/ui-07-pagination-downloads.png)

### Вкладка Results history

*Скриншот: таблица Recent runs (зебра-строки, статусы-плашки, колонка Actions с **Open**).*

![История запусков](docs/screenshots/ui-08-history-table.png)

### Массовые действия в истории

*Скриншот: отмеченные строки, панель **Select all** / **Delete selected** для прогонов.*

![Массовые действия в истории](docs/screenshots/ui-09-history-bulk-actions.png)

---

## Возможности интерфейса (кратко)

| Область | Возможности |
|---------|-------------|
| **Запуск** | Вставка той же CLI-строки, что и в терминале; флаги экспорта CSV и Excel |
| **Мониторинг** | Статус прогона, сводка по страницам и записям |
| **Таблица Results** | Сортировка по названию компании и категории; фильтры; чекбоксы; выбор «все на странице»; удаление выбранных строк из текущего run (с обновлением экспортов на диске) |
| **Постраничность** | Настраиваемое число строк на странице (10–100), общий стиль выпадающих списков с фильтром по сайту |
| **История** | Список недавних run, открытие прогона, множественный выбор, удаление завершённых/неактивных прогонов (активные queued/running не удаляются) |
| **Выгрузки** | Скачивание CSV и XLSX для завершённого прогона с данными |

---

## Overview (EN)

Python command-line application for collecting public local business listings from Yellow Pages by business category and city, with multi-page traversal and CSV export, plus an optional FastAPI dashboard.

The application accepts a search keyword, a US city, and the maximum number of result pages to process. It then opens Yellow Pages search results, extracts listing data, normalizes records, removes duplicates, and exports the final dataset to CSV (and optionally XLSX via the dashboard).

## Business use cases

- Building structured prospect lists for local service categories
- Supporting outreach and lead research workflows
- Reviewing local market coverage in a specific city
- Collecting business directory data for internal analysis
- Preparing inputs for downstream qualification or enrichment steps

## Supported workflow

Current implementation supports:

- One source: Yellow Pages
- One search pattern: `keyword + city + max_pages`
- CLI export: CSV
- Optional **web dashboard** (FastAPI): run jobs in the background, filter/sort results, row selection and bulk delete from a run, run history with bulk delete, download CSV or XLSX per run
- CLI-first execution; dashboard is optional

CSV columns:

- `company_name`
- `website`
- `phone`
- `category`
- `address`
- `city`
- `source_url`

## Features

- Command-line run `python main.py`
- Search URL generation for Yellow Pages
- Multi-page result processing
- Parsing company listing cards
- Record normalization before export
- Basic deduplication
- CSV export
- Logging to console and file
- Graceful handling of blocked pages without crashing the full run

## Project structure

```text
.
├── main.py
├── requirements.txt
├── README.md
├── .gitignore
├── static/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── tests/
│   ├── conftest.py
│   ├── test_cli.py
│   ├── test_dedupe.py
│   ├── test_export.py
│   ├── test_normalizer.py
│   ├── test_xlsx_export.py
│   └── test_yp_search.py
└── src/
    ├── browser_client.py
    ├── cli.py
    ├── config.py
    ├── dedupe.py
    ├── export.py
    ├── logger.py
    ├── models.py
    ├── normalizer.py
    ├── parser.py
    ├── scraper.py
    ├── xlsx_export.py
    ├── yp_search.py
    └── web/
        ├── app.py
        └── run_store.py
```

## Installation

Create and activate a virtual environment.

### macOS / Linux
```bash
python -m venv .venv
source .venv/bin/activate
```

### Windows
```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
playwright install chromium
```

Runtime libraries (see `requirements.txt`): **beautifulsoup4**, **playwright**, **fastapi**, **uvicorn**, **openpyxl** (dashboard + Excel export). Dev/tests: **pytest**. There is **no** `requests` package; see [Fetching: Playwright vs HTTP](#fetching-playwright-vs-http).

## Usage

Example run:

```bash
python main.py --keyword plumber --city "Austin, TX" --max-pages 3
```

### Web dashboard

Start the API and open the UI in a browser (not as a raw `file://` page):

```bash
uvicorn src.web.app:app --host 127.0.0.1 --port 8000
```

Then visit **http://127.0.0.1:8000/** . Paste the same CLI line as in the terminal (or only `--keyword … --city … --max-pages …`). Each run stores artifacts under `output/runs/<run_id>/` (debug HTML/PNG, optional `results.csv` / `results.xlsx`).

Dashboard API highlights:

- `POST /api/runs`, `POST /api/runs/cli` — start runs
- `GET /api/runs`, `POST /api/runs/delete` — list and delete runs (running/queued runs are skipped)
- `GET /api/runs/{id}/results` — paginated, filtered, sorted results
- `POST /api/runs/{id}/results/delete` — remove selected rows from a completed run and refresh exports when enabled

Optional: set **`SCRAPER_OUTPUT_DIR`** to change where run folders are written.

## Output

The application writes generated files into the `output/` directory:

- `yellowpages_results.csv` — final business records
- `scraper.log` — execution log
- `debug_search_page_*.html` — saved HTML snapshots
- `debug_search_page_*.png` — saved page screenshots

## Testing

Run tests with:

```bash
pytest
```

If `pytest` does not see the `src` package in your environment, the project includes `tests/conftest.py`, which adds the project root to the Python import path before test collection.

## Fetching: Playwright vs HTTP

- **Current design:** search pages are loaded with **Playwright** (Chromium) via `src/browser_client.py`. HTML is then parsed with Beautiful Soup. This matches how Yellow Pages often serves content and anti-bot challenges.
- **`requests` is not a project dependency.** It was removed to keep the install minimal; the codebase does not ship an alternate HTTP-only client.
- **If you add a simple HTTP fetch path** (e.g. `requests` + static HTML): add `requests` to `requirements.txt`, implement your client (for example under `src/`), and wire it in `main.py` / the scraper as needed. Document the trade-off (speed vs. reliability) in your fork.
- **If you only use Playwright** (default): no change required.

## Operational notes

- Yellow Pages may return Cloudflare block pages during some runs.
- The scraper is designed to continue processing remaining pages when a single page is blocked.
- `website` is not guaranteed to be present for every listing.
- Some address parsing details can be refined further depending on downstream requirements.
