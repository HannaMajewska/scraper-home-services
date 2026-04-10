# Data model for one business listing and row dict for CSV export.
from dataclasses import asdict, dataclass


@dataclass(slots=True)
class BusinessListing:
    company_name: str
    website: str
    phone: str
    category: str
    address: str
    city: str
    source_url: str

    def to_row(self) -> dict[str, str]:
        return asdict(self)
