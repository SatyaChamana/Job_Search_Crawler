import re
import logging
from typing import List

from bs4 import BeautifulSoup

from crawler.browser import fetch_rendered_html
from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)


class VisaParser(ParserBase):
    """Parser for Visa's careers site. Requires browser rendering."""

    def fetch_and_parse(self) -> List[JobPosting]:
        try:
            logger.info(f"[{self.site_name}] Fetching with browser...")
            wait_ms = self.site_config.get("wait_ms", 10000)
            html = fetch_rendered_html(self.url, wait_ms=wait_ms)
            jobs = self._parse_html(html)
            logger.info(f"[{self.site_name}] Found {len(jobs)} jobs")
            return self.filter_by_title(jobs)
        except Exception as e:
            logger.error(f"[{self.site_name}] Visa parsing failed: {e}")
            return []

    def _parse_html(self, html: str) -> List[JobPosting]:
        soup = BeautifulSoup(html, "html.parser")
        jobs = []
        seen_ids = set()

        links = soup.find_all("a", href=re.compile(r"/en/jobs/REF\w+"))
        for link in links:
            href = link.get("href", "")
            title = link.get_text(strip=True)

            if not title or len(title) < 5:
                continue

            m = re.search(r"/jobs/(REF\w+)", href)
            if not m:
                continue
            job_id = m.group(1)

            if job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            # Extract location from parent
            location = ""
            card = link.find_parent(["div", "li", "article"])
            if card:
                for span in card.find_all(["span", "p", "div"]):
                    text = span.get_text(strip=True)
                    if text != title and len(text) < 80 and any(
                        c in text for c in [
                            "Austin", "San Francisco", "Foster City", "Atlanta",
                            "Denver", "Bellevue", "Highlands Ranch", "Lehi",
                            "Los Angeles", "Mentor", "Miami", "New York",
                            "Washington", "Wilmington", "Ashburn", "TX", "CA",
                        ]
                    ):
                        location = text
                        break

            # Build proper URL (avoid double prefix)
            if href.startswith("http"):
                job_url = href
            else:
                job_url = f"https://corporate.visa.com{href}"

            jobs.append(JobPosting(
                job_id=job_id,
                title=title,
                location=location,
                url=job_url,
                company="Visa",
                requisition_id=job_id,
            ))

        return jobs
