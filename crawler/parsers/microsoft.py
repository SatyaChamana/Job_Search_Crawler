import re
import logging
from typing import List

from bs4 import BeautifulSoup

from crawler.browser import fetch_rendered_html
from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)

# Microsoft's search page is an SPA inside an iframe. The actual content
# is served from careers.microsoft.com/v2/... which we load directly.
MS_SEARCH_URL = "https://careers.microsoft.com/v2/global/en/home.html"


class MicrosoftParser(ParserBase):
    """Parser for Microsoft careers. Uses browser rendering on
    the inner SPA frame URL for best results.
    """

    def fetch_and_parse(self) -> List[JobPosting]:
        try:
            logger.info(f"[{self.site_name}] Fetching with browser...")
            jobs = self._try_browser()
            logger.info(f"[{self.site_name}] Found {len(jobs)} jobs")
            return self.filter_by_title(jobs)
        except Exception as e:
            logger.error(f"[{self.site_name}] Microsoft parsing failed: {e}")
            return []

    def _try_browser(self) -> List[JobPosting]:
        from playwright.sync_api import sync_playwright

        search_query = self.site_config.get("search_text", "SDE")

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

            # Intercept the search API response
            api_data = {}

            def handle_response(response):
                if "search/api" in response.url and response.status == 200:
                    try:
                        api_data["result"] = response.json()
                    except Exception:
                        pass

            page.on("response", handle_response)

            # Load the page and wait for results
            page.goto(self.url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(15000)

            # Try parsing from intercepted API data
            if api_data.get("result"):
                jobs = self._parse_api(api_data["result"])
                if jobs:
                    context.close()
                    browser.close()
                    return jobs

            # Fallback: parse rendered HTML
            html = page.content()
            context.close()
            browser.close()

        return self._parse_html(html)

    def _parse_api(self, data: dict) -> List[JobPosting]:
        """Parse Microsoft search API response."""
        result = data.get("operationResult", {}).get("result", {})
        job_list = result.get("jobs", [])
        jobs = []

        for item in job_list:
            job_id = str(item.get("jobId", ""))
            title = item.get("title", "")
            props = item.get("properties", {})
            location = props.get("primaryLocation", props.get("location", ""))
            date_posted = props.get("postedDate", "")

            job_url = f"https://jobs.careers.microsoft.com/global/en/job/{job_id}"

            jobs.append(JobPosting(
                job_id=job_id,
                title=title,
                location=location,
                url=job_url,
                company="Microsoft",
                date_posted=date_posted,
            ))

        return jobs

    def _parse_html(self, html: str) -> List[JobPosting]:
        """Fallback HTML parsing."""
        soup = BeautifulSoup(html, "html.parser")
        jobs = []
        seen_ids = set()

        for link in soup.find_all("a"):
            href = link.get("href", "")
            text = link.get_text(strip=True)
            if not text or len(text) < 5:
                continue

            m = re.search(r"/job/(\d+)", href)
            if not m:
                continue

            job_id = m.group(1)
            if job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            job_url = href
            if not href.startswith("http"):
                job_url = f"https://jobs.careers.microsoft.com{href}"

            jobs.append(JobPosting(
                job_id=job_id,
                title=text,
                location="",
                url=job_url,
                company="Microsoft",
            ))

        return jobs
