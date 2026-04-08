from src.models import BusinessListing
from src.normalizer import extract_city_from_address, normalize_listing, normalize_url


def test_normalize_url_for_relative_yellowpages_path() -> None:
    result = normalize_url("/austin-tx/mip/test-company-123")

    assert result == "https://www.yellowpages.com/austin-tx/mip/test-company-123"


def test_extract_city_from_address() -> None:
    result = extract_city_from_address("123 Main St, Austin, TX")

    assert result == "Austin, TX"


def test_normalize_listing_fills_city_from_address_when_city_is_empty() -> None:
    listing = BusinessListing(
        company_name="  Alpha Plumbing  ",
        website="/austin-tx/mip/alpha-plumbing-1",
        phone="  (512) 555-0100  ",
        category="  Plumbers ",
        address=" 123 Main St, Austin, TX ",
        city="",
        source_url="/austin-tx/mip/alpha-plumbing-1",
    )

    normalized = normalize_listing(listing)

    assert normalized.company_name == "Alpha Plumbing"
    assert normalized.website == "https://www.yellowpages.com/austin-tx/mip/alpha-plumbing-1"
    assert normalized.phone == "(512) 555-0100"
    assert normalized.category == "Plumbers"
    assert normalized.address == "123 Main St, Austin, TX"
    assert normalized.city == "Austin, TX"
    assert normalized.source_url == "https://www.yellowpages.com/austin-tx/mip/alpha-plumbing-1"