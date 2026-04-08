from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


class YellowPagesBrowserClient:
    def __init__(self, headless: bool = True, timeout_ms: int = 30000) -> None:
        self.headless = headless
        self.timeout_ms = timeout_ms

    def fetch_search_page_html(self, url: str, screenshot_path: Path) -> str:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=self.headless,
                slow_mo=300,
            )

            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1440, "height": 2200},
                locale="en-US",
            )

            page = context.new_page()
            page.set_default_timeout(self.timeout_ms)

            try:
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_timeout(5000)
                page.screenshot(path=str(screenshot_path), full_page=True)
                html = page.content()
                return html
            except PlaywrightTimeoutError as exc:
                page.screenshot(path=str(screenshot_path), full_page=True)
                raise RuntimeError(
                    f"Playwright timeout while loading page: {url}"
                ) from exc
            finally:
                context.close()
                browser.close()
