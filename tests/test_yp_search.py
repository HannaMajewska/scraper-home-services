from src.yp_search import build_search_url


def test_build_search_url_for_first_page() -> None:
    url = build_search_url("plumber", "Austin, TX", page=1)

    assert url == (
        "https://www.yellowpages.com/search"
        "?search_terms=plumber&geo_location_terms=Austin%2C+TX"
    )


def test_build_search_url_for_second_page() -> None:
    url = build_search_url("plumber", "Austin, TX", page=2)

    assert url == (
        "https://www.yellowpages.com/search"
        "?search_terms=plumber&geo_location_terms=Austin%2C+TX&page=2"
    )