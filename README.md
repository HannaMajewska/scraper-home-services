# Local Business Directory Scraper for USA Home Services

Python command-line application for collecting public local business listings from Yellow Pages by business category and city, with multi-page traversal and CSV export.

## Overview

This project was designed as a practical data collection utility for business and marketing workflows where structured local business records are needed for research, outreach preparation, market mapping, and directory visibility analysis.

The application accepts a search keyword, a US city, and the maximum number of result pages to process. It then opens Yellow Pages search results, extracts listing data, normalizes records, removes duplicates, and exports the final dataset to CSV.

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
- One export format: CSV
- CLI-first execution

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
├── tests/
│   ├── conftest.py
│   ├── test_cli.py
│   ├── test_dedupe.py
│   ├── test_export.py
│   ├── test_normalizer.py
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
    └── yp_search.py
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

Runtime libraries (see `requirements.txt`): **beautifulsoup4**, **playwright**. Dev/tests: **pytest**. There is **no** `requests` package; see [Fetching: Playwright vs HTTP](#fetching-playwright-vs-http).

## Usage

Example run:

```bash
python main.py --keyword plumber --city "Austin, TX" --max-pages 3
```

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