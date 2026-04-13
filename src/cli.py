# Command-line argument parsing for the scraper and dashboard API.
from __future__ import annotations

import argparse
import shlex


def pages_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("max_pages must be >= 1")
    return parsed


class _ApiArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


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


def build_api_parser() -> _ApiArgumentParser:
    """Parser for dashboard/API: only --keyword, --city, --max-pages (no script name)."""
    parser = _ApiArgumentParser(add_help=False)
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
    return parser


def argv_from_command_line(command: str) -> list[str]:
    """Split a pasted terminal line; strip optional `python main.py` prefix."""
    line = command.strip()
    if not line:
        return []
    try:
        parts = shlex.split(line)
    except ValueError:
        return []
    while parts and parts[0] in ("python", "python3", "py"):
        parts = parts[1:]
    if parts and parts[0].endswith("main.py"):
        parts = parts[1:]
    return parts


def parse_args_for_api(argv: list[str]) -> argparse.Namespace:
    if not argv:
        raise ValueError("No arguments to parse.")
    parser = build_api_parser()
    return parser.parse_args(argv)
