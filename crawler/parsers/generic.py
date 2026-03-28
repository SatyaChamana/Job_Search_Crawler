import re
import json
import logging
from typing import List
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from crawler.fetcher import fetch_page
from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)


class GenericHTMLParser(ParserBase):
    """Generic HTML parser for career sites.

    Tries multiple strategies to extract job listings:
    1. __NEXT_DATA__ embedded JSON (Next.js sites)
    2. Links matching job URL patterns
    3. Common job card HTML structures

    For JavaScript-rendered SPAs, this parser may return limited results.
    Consider adding Selenium/Playwright support for such sites.
    """

    def fetch_and_parse(self) -> List[JobPosting]:
        try:
            logger.info(f"[{self.site_name}] Fetching page with generic parser...")
            response = fetch_page(self.url)
            jobs = self._parse(response.text)
            if not jobs:
                logger.warning(
                    f"[{self.site_name}] No jobs found. This site may require "
                    "JavaScript rendering (Selenium/Playwright)."
                )
            else:
                logger.info(f"[{self.site_name}] Found {len(jobs)} jobs")
            return self.filter_by_title(jobs)
        except Exception as e:
            logger.error(f"[{self.site_name}] Generic parser failed: {e}")
            return []

    def _parse(self, html: str) -> List[JobPosting]:
        # Strategy 1: Try __NEXT_DATA__
        jobs = self._try_next_data(html)
        if jobs:
            return jobs

        # Strategy 2: Try HTML link parsing
        jobs = self._try_html_links(html)
        return jobs

    def _try_next_data(self, html: str) -> List[JobPosting]:
        """Try to extract jobs from Next.js __NEXT_DATA__."""
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

        # Look for common job list keys
        for key in ["jobs", "results", "jobPostings", "positions", "listings", "items"]:
            items = data.get(key)
            if isinstance(items, list) and items and isinstance(items[0], dict):
                for item in items:
                    job = self._dict_to_job(item)
                    if job:
                        jobs.append(job)
                if jobs:
                    return jobs

        # Recurse into dict values
        for val in data.values():
            if isinstance(val, dict):
                jobs = self._extract_jobs_from_dict(val, depth + 1)
                if jobs:
                    return jobs

        return jobs

    def _dict_to_job(self, item: dict) -> JobPosting:
        """Convert a dictionary to a JobPosting if it has enough fields."""
        title = (
            item.get("title")
            or item.get("name")
            or item.get("jobTitle")
            or item.get("posting_name")
            or ""
        )
        job_id = str(
            item.get("id")
            or item.get("job_id")
            or item.get("jobId")
            or item.get("requisitionId")
            or ""
        )

        if not title or not job_id:
            return None

        location = item.get("location") or item.get("locationName") or item.get("locations") or ""
        if isinstance(location, list):
            location = ", ".join(str(l) for l in location)
        elif isinstance(location, dict):
            location = location.get("name", str(location))

        url = (
            item.get("url")
            or item.get("absolute_url")
            or item.get("canonical_url")
            or item.get("externalPath")
            or ""
        )
        date_posted = str(
            item.get("date_posted")
            or item.get("created_at")
            or item.get("postedOn")
            or item.get("postedDate")
            or ""
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
        """Try to find job listings from HTML links."""
        soup = BeautifulSoup(html, "html.parser")
        jobs = []
        seen_ids = set()

        # Get the base domain
        parsed = urlparse(self.url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Common job URL patterns
        job_patterns = [
            r"/jobs?/\d+",
            r"/positions?/\d+",
            r"/job-detail",
            r"/career",
            r"/opening",
            r"/requisition",
        ]
        combined = "|".join(job_patterns)

        links = soup.find_all("a", href=re.compile(combined, re.IGNORECASE))
        for link in links:
            href = link.get("href", "")
            title = link.get_text(strip=True)

            if not title or len(title) < 5:
                continue

            # Try to extract a numeric ID
            m = re.search(r"/(\d{4,})", href)
            if not m:
                m = re.search(r"/([a-zA-Z0-9-]{5,})/?\s*$", href)
            if not m:
                continue

            job_id = m.group(1)
            if job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            job_url = urljoin(base_url, href)

            # Location from parent
            location = ""
            card = link.find_parent(["div", "li", "article", "tr"])
            if card:
                loc_el = card.find(
                    class_=re.compile(r"location|city|region", re.IGNORECASE)
                )
                if loc_el:
                    location = loc_el.get_text(strip=True)

            jobs.append(JobPosting(
                job_id=job_id,
                title=title,
                location=location,
                url=job_url,
                company=self.site_name,
            ))

        return jobs
