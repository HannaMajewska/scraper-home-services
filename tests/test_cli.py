# Tests for pages_int (--max-pages validation).
import argparse
import pytest

from src.cli import pages_int


def test_pages_int_returns_valid_integer() -> None:
    assert pages_int("3") == 3


def test_pages_int_raises_for_zero() -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        pages_int("0")


def test_pages_int_raises_for_negative_number() -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        pages_int("-2")