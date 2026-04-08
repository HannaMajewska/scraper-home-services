from urllib.parse import urljoin

from src.models import BusinessListing


YELLOWPAGES_BASE_URL = "https://www.yellowpages.com"


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.strip().split())


def normalize_url(value: str) -> str:
    cleaned = clean_text(value)

    if not cleaned:
        return ""

    if cleaned.startswith("http://") or cleaned.startswith("https://"):
        return cleaned

    if cleaned.startswith("/"):
        return urljoin(YELLOWPAGES_BASE_URL, cleaned)

    return cleaned


def extract_city_from_address(address: str) -> str:
    cleaned_address = clean_text(address)

    if not cleaned_address or "," not in cleaned_address:
        return ""

    parts = [part.strip() for part in cleaned_address.split(",") if part.strip()]
    if len(parts) < 2:
        return ""

    return ", ".join(parts[-2:])


def normalize_listing(listing: BusinessListing) -> BusinessListing:
    return BusinessListing(
        company_name=clean_text(listing.company_name),
        website=normalize_url(listing.website),
        phone=clean_text(listing.phone),
        category=clean_text(listing.category),
        address=clean_text(listing.address),
        city=clean_text(listing.city) or extract_city_from_address(listing.address),
        source_url=normalize_url(listing.source_url),
    )


def is_valid_listing(listing: BusinessListing) -> bool:
    return bool(clean_text(listing.company_name))