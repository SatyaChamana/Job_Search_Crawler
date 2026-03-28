import re
import logging
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler.fetcher import fetch_page
from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)


class CaterpillarParser(ParserBase):
    """Parser for Caterpillar's careers site using HTML parsing."""

    def fetch_and_parse(self) -> List[JobPosting]:
        try:
            logger.info(f"[{self.site_name}] Fetching Caterpillar careers page...")
            response = fetch_page(self.url)
            jobs = self._parse_html(response.text)
            logger.info(f"[{self.site_name}] Found {len(jobs)} jobs")
            return self.filter_by_title(jobs)
        except Exception as e:
            logger.error(f"[{self.site_name}] Failed to parse Caterpillar careers: {e}")
            return []

    def _parse_html(self, html: str) -> List[JobPosting]:
        soup = BeautifulSoup(html, "html.parser")
        jobs = []
        seen_ids = set()

        # Caterpillar job links follow pattern: /en/jobs/{req_id}/{slug}/
        links = soup.find_all("a", href=re.compile(r"/en/jobs/[a-zA-Z0-9]+/"))
        for link in links:
            href = link.get("href", "")
            title = link.get_text(strip=True)

            # Skip nav links
            if not title or title in ("Jobs", "English") or "Saved" in title or len(title) < 5:
                continue

            # Extract requisition ID from URL (e.g., /en/jobs/r0000359620/software-engineer/)
            m = re.search(r"/en/jobs/([a-zA-Z0-9]+)/", href)
            if not m:
                continue

            job_id = m.group(1)
            if job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            job_url = urljoin("https://careers.caterpillar.com", href)

            # Try to find location from parent card
            location = ""
            card = link.find_parent(["div", "li", "article"])
            if card:
                loc_el = card.find(class_=re.compile(r"location|city|region", re.IGNORECASE))
                if loc_el:
                    location = loc_el.get_text(strip=True)

            jobs.append(JobPosting(
                job_id=job_id,
                title=title,
                location=location,
                url=job_url,
                company="Caterpillar",
                requisition_id=job_id,
            ))

        return jobs
