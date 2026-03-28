import re
import json
import logging
from typing import List

from bs4 import BeautifulSoup

from crawler.browser import fetch_rendered_html
from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)


class MetaParser(ParserBase):
    """Parser for Meta careers. Uses browser rendering and extracts
    job data from embedded data-sjs scripts or rendered HTML.
    """

    def fetch_and_parse(self) -> List[JobPosting]:
        try:
            logger.info(f"[{self.site_name}] Fetching with browser...")
            jobs = self._try_browser()
            logger.info(f"[{self.site_name}] Found {len(jobs)} jobs")
            return self.filter_by_title(jobs)
        except Exception as e:
            logger.error(f"[{self.site_name}] Meta parsing failed: {e}")
            return []

    def _try_browser(self) -> List[JobPosting]:
        from playwright.sync_api import sync_playwright

        api_responses = []

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

            # Intercept API calls for job data
            def handle_response(response):
                url = response.url
                if ("graphql" in url or "api" in url) and response.status == 200:
                    ct = response.headers.get("content-type", "")
                    if "json" in ct:
                        try:
                            api_responses.append(response.json())
                        except Exception:
                            pass

            page.on("response", handle_response)
            page.goto(self.url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(12000)
            html = page.content()
            context.close()
            browser.close()

        # Try intercepted API data
        for data in api_responses:
            jobs = self._try_extract_from_api(data)
            if jobs:
                return jobs

        # Try embedded data-sjs scripts
        jobs = self._parse_data_sjs(html)
        if jobs:
            return jobs

        # Fallback: parse role="link" elements
        return self._parse_role_links(html)

    def _try_extract_from_api(self, data, depth=0) -> List[JobPosting]:
        """Recursively search API response for job listings."""
        if depth > 5:
            return []
        if isinstance(data, dict):
            for key in ["jobs", "results", "edges", "nodes", "job_search"]:
                if key in data:
                    items = data[key]
                    if isinstance(items, list):
                        jobs = []
                        for item in items:
                            node = item.get("node", item) if isinstance(item, dict) else item
                            if isinstance(node, dict):
                                job = self._node_to_job(node)
                                if job:
                                    jobs.append(job)
                        if jobs:
                            return jobs
            for val in data.values():
                result = self._try_extract_from_api(val, depth + 1)
                if result:
                    return result
        elif isinstance(data, list):
            for item in data[:5]:
                result = self._try_extract_from_api(item, depth + 1)
                if result:
                    return result
        return []

    def _node_to_job(self, node: dict) -> JobPosting:
        title = node.get("title") or node.get("name") or ""
        job_id = str(node.get("id") or node.get("job_id") or "")
        if not title or not job_id:
            return None

        location = node.get("location") or ""
        if isinstance(location, list):
            location = ", ".join(str(l) for l in location)

        url = node.get("url") or node.get("path") or ""
        if url and not url.startswith("http"):
            url = f"https://www.metacareers.com{url}"

        return JobPosting(
            job_id=job_id,
            title=title,
            location=str(location),
            url=url,
            company="Meta",
        )

    def _parse_data_sjs(self, html: str) -> List[JobPosting]:
        """Parse Meta's data-sjs embedded JSON scripts."""
        soup = BeautifulSoup(html, "html.parser")
        jobs = []

        for script in soup.find_all("script", attrs={"data-sjs": True}):
            text = script.string or ""
            if "title" not in text.lower() or len(text) < 100:
                continue
            try:
                data = json.loads(text)
                found = self._try_extract_from_api(data)
                if found:
                    return found
            except json.JSONDecodeError:
                continue

        return jobs

    def _parse_role_links(self, html: str) -> List[JobPosting]:
        """Fallback: extract from role='link' elements."""
        soup = BeautifulSoup(html, "html.parser")
        jobs = []
        seen = set()

        for el in soup.find_all(attrs={"role": "link"}):
            text = el.get_text(strip=True)
            if not text or len(text) < 10 or len(text) > 120:
                continue
            if not any(kw in text.lower() for kw in ["engineer", "software", "developer"]):
                continue

            # Try to find a link
            a = el.find("a")
            href = a.get("href", "") if a else ""
            m = re.search(r"/(\d{5,})", href or text)
            job_id = m.group(1) if m else str(hash(text))[:8]

            if job_id in seen:
                continue
            seen.add(job_id)

            url = href
            if url and not url.startswith("http"):
                url = f"https://www.metacareers.com{url}"

            jobs.append(JobPosting(
                job_id=job_id,
                title=text,
                location="",
                url=url,
                company="Meta",
            ))

        return jobs
