import argparse


def pages_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("max_pages must be >= 1")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Local Business Directory Scraper for USA Home Services"
    )

    parser.add_argument(
        "--keyword",
        required=True,
        help='Business keyword, for example: "plumber"',
    )
    parser.add_argument(
        "--city",
        required=True,
        help='City and state, for example: "Austin, TX"',
    )
    parser.add_argument(
        "--max-pages",
        required=True,
        type=pages_int,
        help="Maximum number of search result pages to process",
    )

    return parser.parse_args()
