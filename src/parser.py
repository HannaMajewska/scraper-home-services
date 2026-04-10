# Parses search result HTML: listing cards and block-page markers (e.g. Cloudflare).
from bs4 import BeautifulSoup

from src.models import BusinessListing
from src.normalizer import clean_text, is_valid_listing, normalize_listing

RESULT_CARD_SELECTORS = [
    "div.search-results.organic div.result",
    "div.result",
    ".result",
    ".organic .result",
    "#main-content .result",
]


def extract_text(node, selector: str) -> str:
    found = node.select_one(selector)
    if found is None:
        return ""
    return clean_text(found.get_text(" ", strip=True))


def extract_attr(node, selector: str, attr_name: str) -> str:
    found = node.select_one(selector)
    if found is None:
        return ""

    value = found.get(attr_name, "")
    if value is None:
        return ""

    return clean_text(value)


def is_block_page(html: str) -> bool:
    lowered = html.lower()

    block_markers = [
        "attention required! | cloudflare",
        "sorry, you have been blocked",
        "cf-error-details",
        "cloudflare ray id",
        "unable to access www.yellowpages.com",
    ]

    return any(marker in lowered for marker in block_markers)


def find_result_cards(soup: BeautifulSoup) -> list:
    for selector in RESULT_CARD_SELECTORS:
        cards = soup.select(selector)
        cards_with_name = [card for card in cards if card.select_one("a.business-name")]
        if cards_with_name:
            return cards_with_name
    return []


def parse_search_results(html: str) -> list[BusinessListing]:
    if is_block_page(html):
        return []

    soup = BeautifulSoup(html, "html.parser")
    result_cards = find_result_cards(soup)

    listings: list[BusinessListing] = []

    for card in result_cards:
        raw_listing = BusinessListing(
            company_name=extract_text(card, "a.business-name"),
            website=extract_attr(card, "a.track-visit-website", "href"),
            phone=extract_text(card, ".phones"),
            category=extract_text(card, ".categories"),
            address=extract_text(card, ".adr"),
            city="",
            source_url=extract_attr(card, "a.business-name", "href"),
        )

        listing = normalize_listing(raw_listing)

        if not is_valid_listing(listing):
            continue

        listings.append(listing)

    return listings
