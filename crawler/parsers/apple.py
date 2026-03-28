import re
import logging
from typing import List

from bs4 import BeautifulSoup

from crawler.fetcher import fetch_page
from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)


class AppleParser(ParserBase):
    """Parser for Apple's careers site (jobs.apple.com) using HTML parsing."""

    def fetch_and_parse(self) -> List[JobPosting]:
        try:
            logger.info(f"[{self.site_name}] Fetching Apple careers page...")
            response = fetch_page(self.url)
            jobs = self._parse_html(response.text)
            logger.info(f"[{self.site_name}] Found {len(jobs)} jobs")
            return self.filter_by_title(jobs)
        except Exception as e:
            logger.error(f"[{self.site_name}] Failed to parse Apple careers: {e}")
            return []

    def _parse_html(self, html: str) -> List[JobPosting]:
        soup = BeautifulSoup(html, "html.parser")
        jobs = []
        seen_ids = set()

        job_list = soup.find(id="search-job-list")
        if not job_list:
            logger.warning(f"[{self.site_name}] Could not find #search-job-list")
            return jobs

        items = job_list.find_all("li", recursive=False)
        for item in items:
            link = item.find("a", href=re.compile(r"/en-us/details/"))
            if not link:
                continue

            title = link.get_text(strip=True)
            href = link["href"]

            # Extract job ID from URL
            m = re.search(r"/details/(\d+)", href)
            if not m:
                continue
            job_id = m.group(1)

            if job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            # Extract location from spans
            location = ""
            date_posted = ""
            for span in item.find_all("span"):
                text = span.get_text(strip=True)
                if not text or text == title or "See full" in text:
                    continue
                if re.match(r"[A-Z][a-z]+ \d{2}, \d{4}", text):
                    date_posted = text
                elif any(x in text for x in [
                    "San", "New", "Austin", "Seattle", "Cupertino", "CA", "NY",
                    "TX", "WA", "Remote", "Chicago", "Boston",
                ]):
                    location = text

            # Fallback: try location-classed element
            if not location:
                loc_el = item.find(class_=re.compile(r"location", re.IGNORECASE))
                if loc_el:
                    location = loc_el.get_text(strip=True).replace("Location", "").strip()

            job_url = f"https://jobs.apple.com{href}" if href.startswith("/") else href

            jobs.append(JobPosting(
                job_id=job_id,
                title=title,
                location=location,
                url=job_url,
                company="Apple",
                date_posted=date_posted,
            ))

        return jobs
