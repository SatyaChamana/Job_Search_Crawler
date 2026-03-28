import re
import json
import logging
from typing import List
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from crawler.fetcher import fetch_page
from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)

# Common URL patterns that indicate job detail pages
JOB_URL_PATTERNS = [
    r"/jobs?/\d+",
    r"/jobs/[a-z0-9][-a-z0-9]+",
    r"/positions?/\d+",
    r"/roles?/\d+",
    r"/careers/job/\d+",
    r"/career/job/\d+",
    r"/global/en/job/\d+",
    r"/en/jobs/REF\w+",
    r"/job-detail",
    r"/opening",
    r"/requisition",
]


class GenericHTMLParser(ParserBase):
    """Generic parser that tries static HTML first, then falls back to
    Playwright browser rendering for JavaScript-heavy SPA sites.
    """

    def fetch_and_parse(self) -> List[JobPosting]:
        # Strategy 1: try static HTML (fast, no browser needed)
        try:
            logger.info(f"[{self.site_name}] Trying static HTML fetch...")
            response = fetch_page(self.url)
            jobs = self._parse(response.text)
            if jobs:
                logger.info(f"[{self.site_name}] Static HTML found {len(jobs)} jobs")
                return self.filter_by_title(jobs)
        except Exception as e:
            logger.warning(f"[{self.site_name}] Static fetch failed: {e}")

        # Strategy 2: browser rendering
        try:
            logger.info(f"[{self.site_name}] Falling back to browser rendering...")
            html = self._fetch_with_browser()
            jobs = self._parse(html)
            if jobs:
                logger.info(f"[{self.site_name}] Browser rendering found {len(jobs)} jobs")
            else:
                logger.warning(
                    f"[{self.site_name}] No jobs found even with browser rendering."
                )
            return self.filter_by_title(jobs)
        except Exception as e:
            logger.error(f"[{self.site_name}] Browser rendering failed: {e}")
            return []

    def _fetch_with_browser(self) -> str:
        from crawler.browser import fetch_rendered_html

        wait_selector = self.site_config.get("wait_selector")
        wait_ms = self.site_config.get("wait_ms", 8000)
        return fetch_rendered_html(
            self.url, wait_selector=wait_selector, wait_ms=wait_ms
        )

    def _parse(self, html: str) -> List[JobPosting]:
        # Try __NEXT_DATA__ first
        jobs = self._try_next_data(html)
        if jobs:
            return jobs

        # Try HTML link parsing
        return self._try_html_links(html)

    def _try_next_data(self, html: str) -> List[JobPosting]:
        """Extract jobs from Next.js __NEXT_DATA__."""
        m = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html
        )
        if not m:
            return []
        try:
            data = json.loads(m.group(1))
            props = data.get("props", {}).get("pageProps", {})
            return self._extract_jobs_from_dict(props)
        except (json.JSONDecodeError, KeyError):
            return []

    def _extract_jobs_from_dict(self, data: dict, depth: int = 0) -> List[JobPosting]:
        """Recursively search for job-like data in nested dicts."""
        if depth > 4:
            return []

        jobs = []
        for key in ["jobs", "results", "jobPostings", "positions", "listings", "items"]:
            items = data.get(key)
            if isinstance(items, list) and items and isinstance(items[0], dict):
                for item in items:
                    job = self._dict_to_job(item)
                    if job:
                        jobs.append(job)
                if jobs:
                    return jobs

        for val in data.values():
            if isinstance(val, dict):
                jobs = self._extract_jobs_from_dict(val, depth + 1)
                if jobs:
                    return jobs
        return jobs

    def _dict_to_job(self, item: dict) -> JobPosting:
        """Convert a dictionary to a JobPosting if it has enough fields."""
        title = (
            item.get("title") or item.get("name") or item.get("jobTitle")
            or item.get("posting_name") or ""
        )
        job_id = str(
            item.get("id") or item.get("job_id") or item.get("jobId")
            or item.get("requisitionId") or ""
        )
        if not title or not job_id:
            return None

        location = item.get("location") or item.get("locationName") or item.get("locations") or ""
        if isinstance(location, list):
            location = ", ".join(str(l) for l in location)
        elif isinstance(location, dict):
            location = location.get("name", str(location))

        url = (
            item.get("url") or item.get("absolute_url")
            or item.get("canonical_url") or item.get("externalPath") or ""
        )
        date_posted = str(
            item.get("date_posted") or item.get("created_at")
            or item.get("postedOn") or item.get("postedDate") or ""
        )

        return JobPosting(
            job_id=job_id,
            title=title,
            location=str(location),
            url=url,
            company=self.site_name,
            date_posted=date_posted,
        )

    def _try_html_links(self, html: str) -> List[JobPosting]:
        """Find job listings from HTML links."""
        soup = BeautifulSoup(html, "html.parser")
        jobs = []
        seen_ids = set()

        parsed = urlparse(self.url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        combined = "|".join(JOB_URL_PATTERNS)
        links = soup.find_all("a", href=re.compile(combined, re.IGNORECASE))

        for link in links:
            href = link.get("href", "")
            title = link.get_text(strip=True)

            if not title or len(title) < 5:
                continue
            # Skip nav/category links
            if title.lower() in ("jobs", "careers", "engineering", "search"):
                continue

            # Extract job ID from URL
            m = re.search(r"/(?:job|jobs|positions?|roles?|requisition)/(\w[\w-]*)", href)
            if not m:
                m = re.search(r"/(\d{4,})", href)
            if not m:
                continue

            job_id = m.group(1)
            if job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            job_url = urljoin(base_url, href)

            # Extract location from parent element
            location = self._extract_location(link)

            jobs.append(JobPosting(
                job_id=job_id,
                title=title,
                location=location,
                url=job_url,
                company=self.site_name,
            ))

        return jobs

    def _extract_location(self, element) -> str:
        """Try to extract location from an element's parent card."""
        card = element.find_parent(["div", "li", "article", "tr"])
        if not card:
            return ""

        # Try location-classed element
        loc_el = card.find(class_=re.compile(r"location|city|region", re.IGNORECASE))
        if loc_el:
            return loc_el.get_text(strip=True)

        # Try text with city names
        for span in card.find_all(["span", "p", "div"]):
            text = span.get_text(strip=True)
            title_text = element.get_text(strip=True)
            if text and text != title_text and len(text) < 80:
                if any(
                    c in text
                    for c in [
                        "San", "New York", "Austin", "Seattle", "Chicago",
                        "Remote", "CA", "NY", "TX", "WA", "United States",
                    ]
                ):
                    return text

        return ""
