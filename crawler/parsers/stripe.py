import re
import logging
from typing import List

from bs4 import BeautifulSoup

from crawler.fetcher import fetch_page
from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)


class StripeParser(ParserBase):
    """Parser for Stripe's careers site using static HTML table parsing."""

    def fetch_and_parse(self) -> List[JobPosting]:
        try:
            logger.info(f"[{self.site_name}] Fetching Stripe careers page...")
            response = fetch_page(self.url)
            jobs = self._parse_html(response.text)
            logger.info(f"[{self.site_name}] Found {len(jobs)} jobs")
            return self.filter_by_title(jobs)
        except Exception as e:
            logger.error(f"[{self.site_name}] Failed to parse Stripe careers: {e}")
            return []

    def _parse_html(self, html: str) -> List[JobPosting]:
        soup = BeautifulSoup(html, "html.parser")
        jobs = []
        seen_ids = set()

        section = soup.find(class_="JobsListingsSection")
        if not section:
            logger.warning(f"[{self.site_name}] Could not find JobsListingsSection")
            return jobs

        rows = section.find_all(class_="TableRow")
        for row in rows:
            cells = row.find_all(class_="TableCell")
            if len(cells) < 2:
                continue

            link = row.find("a", href=re.compile(r"/jobs/listing/"))
            if not link:
                continue

            title = cells[0].get_text(strip=True)
            team = cells[1].get_text(strip=True) if len(cells) > 1 else ""
            location = cells[2].get_text(strip=True) if len(cells) > 2 else ""

            href = link.get("href", "")
            m = re.search(r"/(\d+)$", href)
            if not m:
                continue
            job_id = m.group(1)

            if job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            job_url = f"https://stripe.com{href}" if href.startswith("/") else href

            jobs.append(JobPosting(
                job_id=job_id,
                title=title,
                location=location,
                url=job_url,
                company="Stripe",
            ))

        return jobs
