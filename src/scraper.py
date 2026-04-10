# Walks Yellow Pages search pages: fetch HTML, parse, aggregate per-page stats.
import logging
from dataclasses import dataclass
from pathlib import Path

from src.browser_client import YellowPagesBrowserClient
from src.models import BusinessListing
from src.parser import is_block_page, parse_search_results
from src.yp_search import build_search_url


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PageScrapeResult:
    page_number: int
    url: str
    status: str
    companies_count: int


@dataclass(slots=True)
class ScrapeRunResult:
    companies: list[BusinessListing]
    pages: list[PageScrapeResult]


def scrape_search_results(
    client: YellowPagesBrowserClient,
    keyword: str,
    city: str,
    max_pages: int,
    output_dir: Path,
) -> ScrapeRunResult:
    all_companies: list[BusinessListing] = []
    page_results: list[PageScrapeResult] = []

    for page_number in range(1, max_pages + 1):
        search_url = build_search_url(
            keyword=keyword,
            city=city,
            page=page_number,
        )

        html_file = output_dir / f"debug_search_page_{page_number}.html"
        screenshot_file = output_dir / f"debug_search_page_{page_number}.png"

        logger.info("Fetching page %s: %s", page_number, search_url)

        html = client.fetch_search_page_html(
            url=search_url,
            screenshot_path=screenshot_file,
        )
        html_file.write_text(html, encoding="utf-8")

        if is_block_page(html):
            page_results.append(
                PageScrapeResult(
                    page_number=page_number,
                    url=search_url,
                    status="blocked",
                    companies_count=0,
                )
            )
            logger.warning("Page %s blocked: %s", page_number, search_url)
            continue

        companies = parse_search_results(html)
        all_companies.extend(companies)

        page_results.append(
            PageScrapeResult(
                page_number=page_number,
                url=search_url,
                status="ok",
                companies_count=len(companies),
            )
        )

        logger.info(
            "Page %s parsed successfully, companies=%s",
            page_number,
            len(companies),
        )

    return ScrapeRunResult(
        companies=all_companies,
        pages=page_results,
    )