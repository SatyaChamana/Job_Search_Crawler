import re
import logging
from typing import List

from bs4 import BeautifulSoup

from crawler.fetcher import fetch_page
from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)


class AirbnbParser(ParserBase):
    """Parser for Airbnb's careers site using HTML parsing."""

    def fetch_and_parse(self) -> List[JobPosting]:
        try:
            logger.info(f"[{self.site_name}] Fetching Airbnb careers page...")
            response = fetch_page(self.url)
            jobs = self._parse_html(response.text)
            logger.info(f"[{self.site_name}] Found {len(jobs)} jobs")
            return self.filter_by_title(jobs)
        except Exception as e:
            logger.error(f"[{self.site_name}] Failed to parse Airbnb careers: {e}")
            return []

    def _parse_html(self, html: str) -> List[JobPosting]:
        soup = BeautifulSoup(html, "html.parser")
        jobs = []
        seen_ids = set()

        links = soup.find_all("a", href=re.compile(r"careers\.airbnb\.com/positions/\d+"))
        for link in links:
            href = link.get("href", "")
            m = re.search(r"/positions/(\d+)", href)
            if not m:
                continue

            job_id = m.group(1)
            if job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            title = link.get_text(strip=True)
            if not title:
                continue

            # Try to find location from parent card
            location = ""
            card = link.find_parent(["div", "li", "article"])
            if card:
                loc_el = card.find(class_=re.compile(r"location|city|region", re.IGNORECASE))
                if loc_el:
                    location = loc_el.get_text(strip=True)
                else:
                    # Look for location-like text in spans
                    for span in card.find_all("span"):
                        text = span.get_text(strip=True)
                        if text != title and any(x in text for x in [
                            "US", "Remote", "San Francisco", "New York", "Seattle",
                        ]):
                            location = text
                            break

            jobs.append(JobPosting(
                job_id=job_id,
                title=title,
                location=location,
                url=href,
                company="Airbnb",
            ))

        return jobs
