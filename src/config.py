from dataclasses import dataclass


@dataclass(slots=True)
class RunConfig:
    keyword: str
    city: str
    max_pages: int
