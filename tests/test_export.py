from pathlib import Path

from src.export import export_companies_to_csv
from src.models import BusinessListing


def test_export_companies_to_csv_creates_expected_file(tmp_path: Path) -> None:
    csv_path = tmp_path / "results.csv"

    companies = [
        BusinessListing(
            company_name="Alpha Plumbing",
            website="https://alpha.example.com",
            phone="111-111-1111",
            category="Plumbers",
            address="123 Main St, Austin, TX",
            city="Austin, TX",
            source_url="https://www.yellowpages.com/austin-tx/mip/alpha-plumbing-1",
        )
    ]

    export_companies_to_csv(companies=companies, csv_path=csv_path)

    assert csv_path.exists()

    content = csv_path.read_text(encoding="utf-8")
    lines = content.strip().splitlines()

    assert lines[0] == "company_name,website,phone,category,address,city,source_url"
    assert "Alpha Plumbing" in lines[1]
    assert "https://alpha.example.com" in lines[1]