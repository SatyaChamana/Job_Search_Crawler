import logging
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


def fetch_rendered_html(url: str, wait_selector: str = None, wait_ms: int = 5000, timeout: int = 30000) -> str:
    """Fetch a page using a headless browser and return the fully rendered HTML.

    Args:
        url: The URL to fetch.
        wait_selector: Optional CSS selector to wait for before capturing HTML.
        wait_ms: Milliseconds to wait after page load if no selector given.
        timeout: Navigation timeout in milliseconds.

    Returns:
        The rendered HTML content of the page.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        try:
            page.goto(url, timeout=timeout, wait_until="domcontentloaded")

            if wait_selector:
                try:
                    page.wait_for_selector(wait_selector, timeout=timeout)
                except Exception:
                    logger.warning(
                        f"Selector '{wait_selector}' not found, "
                        f"falling back to {wait_ms}ms wait"
                    )
                    page.wait_for_timeout(wait_ms)
            else:
                page.wait_for_timeout(wait_ms)

            html = page.content()
        finally:
            context.close()
            browser.close()

    return html
