import logging
from typing import List
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import requests
from bs4 import BeautifulSoup

from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)

BASE_URL = "https://www.wellsfargojobs.com"
MAX_PAGES = 20


class WellsFargoParser(ParserBase):
    """Parser for Wells Fargo careers (static HTML with pagination)."""

    def fetch_and_parse(self) -> List[JobPosting]:
        logger.info(f"[{self.site_name}] Fetching Wells Fargo careers...")

        all_jobs = []
        seen_ids = set()

        for page in range(1, MAX_PAGES + 1):
            page_url = self._build_url(page)
            resp = requests.get(
                page_url,
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
                timeout=30,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select(".card.card-job")

            if not cards:
                break

            for card in cards:
                title_el = card.select_one("h2.card-title a")
                if not title_el:
                    continue

                id_el = card.select_one("[data-id]")
                job_id = id_el.get("data-id", "") if id_el else ""
                if not job_id or job_id in seen_ids:
                    continue
                seen_ids.add(job_id)

                title = title_el.get_text(strip=True)
                href = title_el.get("href", "")
                meta_items = card.select("ul.job-meta li.list-inline-item")
                location = meta_items[0].get_text(strip=True) if meta_items else ""
                date_posted = meta_items[1].get_text(strip=True) if len(meta_items) > 1 else ""

                all_jobs.append(JobPosting(
                    job_id=job_id,
                    title=title,
                    location=location,
                    url=f"{BASE_URL}{href}" if href.startswith("/") else href,
                    company=self.site_name,
                    date_posted=date_posted,
                ))

            logger.info(f"[{self.site_name}] Page {page}: {len(cards)} jobs")

        logger.info(f"[{self.site_name}] Found {len(all_jobs)} jobs total")
        return self.filter_by_title(all_jobs)

    def _build_url(self, page: int) -> str:
        parsed = urlparse(self.url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        params["page"] = [str(page)]
        new_query = urlencode(params, doseq=True)
        return urlunparse(parsed._replace(query=new_query))
