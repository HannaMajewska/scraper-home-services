# Builds Yellow Pages search URLs from keyword, city, and page number.
from urllib.parse import urlencode

BASE_SEARCH_URL = "https://www.yellowpages.com/search"


def build_search_url(keyword: str, city: str, page: int = 1) -> str:
    params = {
        "search_terms": keyword.strip(),
        "geo_location_terms": city.strip(),
    }

    if page > 1:
        params["page"] = str(page)

    return f"{BASE_SEARCH_URL}?{urlencode(params)}"
