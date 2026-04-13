# Local Business Directory Scraper for USA Home Services

Python tool for collecting **public** local business listings from **Yellow Pages** by category (keyword) and US city: multi-page traversal, normalization, deduplication, **CSV** / **Excel** export, and an optional **FastAPI web dashboard** to run jobs and work with results.

---

## Business value

- **Faster market data collection** — turn catalog pages into a structured table in one run instead of manual copy-paste.
- **Lower operational cost** — one CLI command or a few clicks in the dashboard replace hours of repetitive work for sales, marketing, and analytics teams.
- **Repeatable process** — search parameters (keyword, city, page depth) are explicit; each run stores outputs and artifacts under a dedicated run folder.
- **Downstream-ready rows** — a single schema (company name, website, phone, category, address, city, source URL) fits CRM import, enrichment pipelines, and reporting.

## Problems this service addresses

| Challenge | How this project helps |
|-----------|------------------------|
| No single list of businesses for a niche and geography | Parses Yellow Pages results for a given keyword and city |
| Duplicates and messy fields when done by hand | Normalizes records and deduplicates before export |
| Need both automation (CLI) and a friendly UI | CLI for scripts and CI; dashboard for operators |
| Unstable pages and bot challenges | Playwright (Chromium); blocked pages do not stop the whole run |
| Need Excel and row-level cleanup | XLSX export; dashboard filters, sorting, and removal of selected rows from a run |

## Product goals

1. **Reliably** extract listing cards from the public directory within normal site use and your own compliance review.
2. **Predictably** deliver tabular data for business workflows.
3. **Smoothly** support the loop **run → monitor → export → edit the list** in the browser without requiring CLI expertise.

---

## Dashboard UI overview

After starting `uvicorn`, open **http://127.0.0.1:8000/**. The UI has two tabs: **Run** (active job and results table) and **Results history** (recent jobs).

Add screenshots under **`docs/screenshots/`** (folder is tracked in the repo). Adjust filenames in the links below if you use different names.

### Header and navigation

*Screenshot: site title, **Run** and **Results history** tabs.*

![Header and tabs](docs/screenshots/ui-01-header-tabs.png)

### Run tab — start a job

*Screenshot: CLI command field, start controls, CSV/XLSX toggles.*

![Scrape launch form](docs/screenshots/ui-02-run-form.png)

### Run tab — run summary

*Screenshot: **Run summary** (keyword, city, status, page and record counters).*

![Run summary](docs/screenshots/ui-03-run-summary.png)

### Run tab — Results table

*Screenshot: results grid (company, website, phone, category, etc.); row checkboxes; sort on **Company name** and **Category**.*

![Results table](docs/screenshots/ui-04-results-table.png)

### Filters and controls

*Screenshot: company search, city/category filters, custom **Any website** dropdown, **Rows per page** in the same visual style, **Apply filters**.*

![Filters and rows per page](docs/screenshots/ui-05-filters-per-page.png)

### Bulk actions on Results

*Screenshot: bar showing **N row(s) selected**, **Select all**, **Delete selected** (visible when at least one row is checked).*

![Results bulk actions](docs/screenshots/ui-06-results-bulk-actions.png)

### Pagination and downloads

*Screenshot: pagination and **Download CSV** / **Download Excel** links.*

![Pagination and downloads](docs/screenshots/ui-07-pagination-downloads.png)

### Results history tab

*Screenshot: **Recent runs** table (zebra rows, status pills, **Open** in Actions).*

![Run history table](docs/screenshots/ui-08-history-table.png)

### Bulk actions in history

*Screenshot: checked rows, **Select all** / **Delete selected** for runs.*

![History bulk actions](docs/screenshots/ui-09-history-bulk-actions.png)

---

## Dashboard capabilities (summary)

| Area | What you can do |
|------|-----------------|
| **Launch** | Paste the same CLI line as in the terminal; enable CSV and/or Excel export |
| **Monitor** | Job status; summary of pages and records |
| **Results table** | Sort by company name and category; filter; row checkboxes; select all on page; delete selected rows from the current run (on-disk exports refresh when enabled) |
| **Pagination** | Rows per page (10–100); custom dropdowns match the **Any website** control |
| **History** | Recent runs; open a run; multi-select; delete finished runs (**queued** / **running** runs are not deleted) |
| **Downloads** | CSV and XLSX for a completed run that has export files |

---

## Overview

The CLI accepts a search keyword, a US city, and a maximum number of result pages. It loads Yellow Pages search results, extracts cards, normalizes fields, removes duplicates, and writes **CSV** (and **XLSX** when using the dashboard with export enabled).

## Business use cases

- Building structured prospect lists for local service categories
- Supporting outreach and lead research workflows
- Reviewing local market coverage in a specific city
- Collecting directory data for internal analysis
- Feeding downstream qualification or enrichment tools

## Supported workflow

- **Source:** Yellow Pages
- **Search shape:** `keyword + city + max_pages`
- **CLI export:** CSV
- **Optional web dashboard (FastAPI):** background jobs; filter/sort/paginate results; row selection and bulk delete within a run; run history with bulk delete; per-run CSV/XLSX download
- **CLI-first** — the dashboard is optional

Exported columns:

- `company_name`
- `website`
- `phone`
- `category`
- `address`
- `city`
- `source_url`

## Features

- CLI entrypoint: `python main.py`
- Yellow Pages search URL construction
- Multi-page processing
- Listing card parsing
- Normalization before export
- Basic deduplication
- CSV export; XLSX via dashboard path
- Console and file logging
- Continues when individual pages are blocked

## Project structure

```text
.
├── main.py
├── requirements.txt
├── README.md
├── .gitignore
├── docs/
│   └── screenshots/ # UI screenshots referenced above (.gitkeep)
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

Runtime libraries (see `requirements.txt`): **beautifulsoup4**, **playwright**, **fastapi**, **uvicorn**, **openpyxl** (dashboard + Excel). Tests: **pytest**. There is **no** `requests` dependency; see [Fetching: Playwright vs HTTP](#fetching-playwright-vs-http).

## Usage

Example CLI run:

```bash
python main.py --keyword plumber --city "Austin, TX" --max-pages 3
```

### Web dashboard

Start the API and open the UI in a browser (not as a raw `file://` page):

```bash
uvicorn src.web.app:app --host 127.0.0.1 --port 8000
```

Then open **http://127.0.0.1:8000/**. Paste the same CLI line as in the terminal (or at least `--keyword … --city … --max-pages …`). Each run stores artifacts under `output/runs/<run_id>/` (debug HTML/PNG, optional `results.csv` / `results.xlsx`).

**Dashboard API (high level)**

- `POST /api/runs`, `POST /api/runs/cli` — start runs
- `GET /api/runs`, `POST /api/runs/delete` — list runs; delete runs (**queued** / **running** are skipped)
- `GET /api/runs/{id}/results` — paginated, filtered, sorted results
- `POST /api/runs/{id}/results/delete` — remove selected rows from a run and refresh on-disk exports when exports are enabled

Optional: set **`SCRAPER_OUTPUT_DIR`** to change the output root for run folders.

## Output

Typical artifacts under `output/`:

- `yellowpages_results.csv` — aggregated records (CLI-style output)
- `scraper.log` — log file
- `debug_search_page_*.html` — HTML snapshots
- `debug_search_page_*.png` — page screenshots

Per-dashboard-run folder: `output/runs/<run_id>/`.

## Testing

```bash
pytest
```

If `pytest` cannot import `src`, use `tests/conftest.py` (adds the project root to `sys.path`).

## Fetching: Playwright vs HTTP

- **Current design:** Playwright (Chromium) loads search pages (`src/browser_client.py`); Beautiful Soup parses HTML. This matches how Yellow Pages often serves content and anti-bot flows.
- **`requests` is not included.** To add a simple HTTP client, add the dependency, implement a client under `src/`, and document speed vs reliability trade-offs.
- **Playwright-only (default):** no change required.

## Operational notes

- Yellow Pages may return Cloudflare or other block pages.
- The scraper continues with remaining pages when one page is blocked.
- `website` may be empty for some listings.
- Address parsing can be tuned for your downstream rules.
