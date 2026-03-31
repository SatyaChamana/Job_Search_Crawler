import logging
from typing import List
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from bs4 import BeautifulSoup

from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)

MAX_PAGES = 15


class GreenhouseParser(ParserBase):
    """Parser for Greenhouse-powered career sites (Waymo, Zoom, etc.).

    Requires browser rendering (sites return 202 for plain requests).
    Parses .job-search-results-card-body cards with h3.card-title links.
    """

    def fetch_and_parse(self) -> List[JobPosting]:
        from crawler.browser import fetch_rendered_html

        wait_ms = self.site_config.get("wait_ms", 8000)
        logger.info(f"[{self.site_name}] Fetching careers via Greenhouse browser...")

        all_jobs = []
        seen_ids = set()

        for page in range(1, MAX_PAGES + 1):
            page_url = self._build_url(page)
            logger.info(f"[{self.site_name}] Loading page {page}...")
            html = fetch_rendered_html(page_url, wait_ms=wait_ms)
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select(".card-body.job-search-results-card-body")

            if not cards:
                break

            for card in cards:
                title_el = card.select_one("h3.card-title a")
                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                href = title_el.get("href", "")
                job_id = href.rstrip("/").split("/")[-1] if href else ""
                if not job_id or job_id in seen_ids:
                    continue
                seen_ids.add(job_id)

                loc_el = card.select_one(".job-component-location span")
                location = loc_el.get_text(strip=True) if loc_el else ""

                all_jobs.append(JobPosting(
                    job_id=job_id,
                    title=title,
                    location=location,
                    url=href,
                    company=self.site_name,
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
