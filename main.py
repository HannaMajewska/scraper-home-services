import logging
from pathlib import Path

from src.browser_client import YellowPagesBrowserClient
from src.cli import parse_args
from src.config import RunConfig
from src.dedupe import deduplicate_companies
from src.export import export_companies_to_csv
from src.logger import setup_logging
from src.scraper import scrape_search_results

logger = logging.getLogger(__name__)


def main() -> None:
    args = parse_args()

    config = RunConfig(
        keyword=args.keyword,
        city=args.city,
        max_pages=args.max_pages,
    )

    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    log_file = output_dir / "scraper.log"
    setup_logging(log_file)

    logger.info("Scraper started")
    logger.info(
        "Run config: keyword=%s city=%s max_pages=%s",
        config.keyword,
        config.city,
        config.max_pages,
    )

    client = YellowPagesBrowserClient(headless=False)

    run_result = scrape_search_results(
        client=client,
        keyword=config.keyword,
        city=config.city,
        max_pages=config.max_pages,
        output_dir=output_dir,
    )

    raw_companies = run_result.companies
    unique_companies = deduplicate_companies(raw_companies)

    csv_file = output_dir / "yellowpages_results.csv"
    export_companies_to_csv(
        companies=unique_companies,
        csv_path=csv_file,
    )

    blocked_pages = [
        page.page_number for page in run_result.pages if page.status == "blocked"
    ]

    logger.info("Scraper finished")
    logger.info("Parsed companies total: %s", len(raw_companies))
    logger.info("Unique companies total: %s", len(unique_companies))
    logger.info("Saved CSV: %s", csv_file)

    if blocked_pages:
        logger.warning("Blocked pages: %s", blocked_pages)

    for index, company in enumerate(unique_companies[:10], start=1):
        logger.info("-" * 60)
        logger.info("Company #%s", index)
        logger.info("company_name=%s", company.company_name)
        logger.info("website=%s", company.website)
        logger.info("phone=%s", company.phone)
        logger.info("category=%s", company.category)
        logger.info("address=%s", company.address)
        logger.info("city=%s", company.city)
        logger.info("source_url=%s", company.source_url)


if __name__ == "__main__":
    main()
