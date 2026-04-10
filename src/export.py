# Exports listings to CSV with field normalization.
import csv
from pathlib import Path

from src.models import BusinessListing
from src.normalizer import normalize_listing

CSV_COLUMNS = [
    "company_name",
    "website",
    "phone",
    "category",
    "address",
    "city",
    "source_url",
]


def export_companies_to_csv(
    companies: list[BusinessListing],
    csv_path: Path,
) -> None:
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()

        for company in companies:
            normalized = normalize_listing(company)
            row = normalized.to_row()

            normalized_row = {
                column: str(row.get(column, "") or "").strip() for column in CSV_COLUMNS
            }

            writer.writerow(normalized_row)
