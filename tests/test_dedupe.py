from src.dedupe import deduplicate_companies
from src.models import BusinessListing


def test_deduplicate_companies_by_source_url() -> None:
    company_a = BusinessListing(
        company_name="Alpha Plumbing",
        website="https://alpha.example.com",
        phone="111-111-1111",
        category="Plumbers",
        address="123 Main St, Austin, TX",
        city="Austin, TX",
        source_url="https://www.yellowpages.com/austin-tx/mip/alpha-plumbing-1",
    )

    company_b = BusinessListing(
        company_name="Alpha Plumbing",
        website="https://alpha.example.com",
        phone="111-111-1111",
        category="Plumbers",
        address="123 Main St, Austin, TX",
        city="Austin, TX",
        source_url="https://www.yellowpages.com/austin-tx/mip/alpha-plumbing-1",
    )

    result = deduplicate_companies([company_a, company_b])

    assert len(result) == 1
    assert result[0].company_name == "Alpha Plumbing"


def test_deduplicate_companies_by_composite_key_when_source_url_missing() -> None:
    company_a = BusinessListing(
        company_name="Beta Plumbing",
        website="",
        phone="222-222-2222",
        category="Plumbers",
        address="500 Oak Ave, Austin, TX",
        city="Austin, TX",
        source_url="",
    )

    company_b = BusinessListing(
        company_name="Beta Plumbing",
        website="",
        phone="222-222-2222",
        category="Plumbers",
        address="500 Oak Ave, Austin, TX",
        city="Austin, TX",
        source_url="",
    )

    result = deduplicate_companies([company_a, company_b])

    assert len(result) == 1
    assert result[0].company_name == "Beta Plumbing"