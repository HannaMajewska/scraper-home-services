# Deduplicates listings by source_url or a composite key (name, phone, address).
from src.models import BusinessListing
from src.normalizer import clean_text


def build_listing_key(listing: BusinessListing) -> str:
    source_url = clean_text(listing.source_url).lower()
    if source_url:
        return f"url::{source_url}"

    company_name = clean_text(listing.company_name).lower()
    phone = clean_text(listing.phone).lower()
    address = clean_text(listing.address).lower()

    return f"composite::{company_name}|{phone}|{address}"


def deduplicate_companies(companies: list[BusinessListing]) -> list[BusinessListing]:
    unique_companies: list[BusinessListing] = []
    seen_keys: set[str] = set()

    for company in companies:
        key = build_listing_key(company)
        if key in seen_keys:
            continue

        seen_keys.add(key)
        unique_companies.append(company)

    return unique_companies
