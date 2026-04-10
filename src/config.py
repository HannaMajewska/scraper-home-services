# Single-run settings: keyword, city, and max result pages.
from dataclasses import dataclass


@dataclass(slots=True)
class RunConfig:
    keyword: str
    city: str
    max_pages: int
