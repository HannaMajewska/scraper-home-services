# Tests for pages_int (--max-pages validation) and API argv parsing.
import argparse
import pytest

from src.cli import (
    argv_from_command_line,
    pages_int,
    parse_args_for_api,
)


def test_pages_int_returns_valid_integer() -> None:
    assert pages_int("3") == 3


def test_pages_int_raises_for_zero() -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        pages_int("0")


def test_pages_int_raises_for_negative_number() -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        pages_int("-2")


def test_argv_from_command_line_strips_python_main() -> None:
    assert argv_from_command_line(
        'python main.py --keyword a --city "B, TX" --max-pages 2'
    ) == ["--keyword", "a", "--city", "B, TX", "--max-pages", "2"]


def test_argv_from_command_line_flags_only() -> None:
    assert argv_from_command_line('--keyword x --city "Y, Z" --max-pages 1') == [
        "--keyword",
        "x",
        "--city",
        "Y, Z",
        "--max-pages",
        "1",
    ]


def test_parse_args_for_api() -> None:
    ns = parse_args_for_api(
        ["--keyword", "plumber", "--city", "Austin, TX", "--max-pages", "3"]
    )
    assert ns.keyword == "plumber"
    assert ns.city == "Austin, TX"
    assert ns.max_pages == 3


def test_parse_args_for_api_raises_on_missing() -> None:
    with pytest.raises(ValueError):
        parse_args_for_api(["--keyword", "only"])