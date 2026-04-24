import logging
from typing import List

import requests
from bs4 import BeautifulSoup

from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)


class AvatureParser(ParserBase):
    """Parser for Avature-powered career sites (Two Sigma, etc.)."""

    def fetch_and_parse(self) -> List[JobPosting]:
        try:
            logger.info(f"[{self.site_name}] Fetching from Avature careers page...")
            jobs = self._fetch_html()
            logger.info(f"[{self.site_name}] Found {len(jobs)} jobs")
            return self.filter_by_title(jobs)
        except Exception as e:
            logger.error(f"[{self.site_name}] Avature fetch failed: {e}")
            return []

    def _fetch_html(self) -> List[JobPosting]:
        url = self.url
        if "jobRecordsPerPage" not in url:
            url += "&jobRecordsPerPage=100" if "?" in url else "?jobRecordsPerPage=100"

        resp = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            },
            timeout=30,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        cards = soup.select(".article__header__text")
        jobs = []
        seen_ids = set()

        for card in cards:
            title_link = card.select_one("h3.article__header__text__title a.link")
            if not title_link:
                continue

            href = title_link.get("href", "")
            job_id = href.rstrip("/").split("/")[-1]
            if not job_id or job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            title = title_link.get_text(strip=True)
            # Two Sigma uses .article__header__content__text > .paragraph_inner-span
            # Bloomberg uses .article__header__text__subtitle > .list-item-location
            loc_el = card.select_one(
                ".article__header__content > .article__header__content__text > .paragraph_inner-span"
            ) or card.select_one(".list-item-location")
            location = loc_el.get_text(strip=True) if loc_el else ""

            jobs.append(JobPosting(
                job_id=job_id,
                title=title,
                location=location,
                url=href,
                company=self.site_name,
            ))

        return jobs
