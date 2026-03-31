import logging
from typing import List

import requests

from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)

MAX_PAGES = 20
PAGE_SIZE = 10


class JibeParser(ParserBase):
    """Parser for careers sites powered by Google Jibe (e.g. DocuSign).

    Uses the /api/jobs JSON endpoint that Jibe sites expose.
    Config keys:
        jibe_base_url: Base URL of the careers site (e.g. https://careers.docusign.com)
        search_text: Search keywords
        location: Optional location filter (e.g. "United States")
    """

    def fetch_and_parse(self) -> List[JobPosting]:
        base_url = self.site_config.get("jibe_base_url", "").rstrip("/")
        if not base_url:
            logger.error(f"[{self.site_name}] No jibe_base_url configured")
            return []

        search_text = self.site_config.get("search_text", "software")
        location = self.site_config.get("location", "")
        api_url = f"{base_url}/api/jobs"

        logger.info(f"[{self.site_name}] Fetching jobs from Jibe API: '{search_text}'")

        all_jobs = []
        seen_ids = set()

        for page in range(1, MAX_PAGES + 1):
            params = {
                "keywords": search_text,
                "sortBy": "posted_date",
                "descending": "true",
                "page": page,
            }
            if location:
                params["location"] = location

            resp = requests.get(
                api_url,
                params=params,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Accept": "application/json",
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            jobs_list = data.get("jobs", [])

            if not jobs_list:
                break

            for item in jobs_list:
                j = item.get("data", {})
                slug = j.get("slug", "")
                if not slug or slug in seen_ids:
                    continue
                seen_ids.add(slug)

                city = j.get("city", "")
                state = j.get("state", "")
                country = j.get("country", "")
                location_parts = [p for p in [city, state, country] if p]
                loc_str = ", ".join(location_parts)

                all_jobs.append(JobPosting(
                    job_id=j.get("req_id", slug),
                    title=j.get("title", ""),
                    location=loc_str,
                    url=f"{base_url}/jobs/{slug}",
                    company=self.site_name,
                    date_posted=j.get("posted_date", ""),
                ))

            total = data.get("count", 0)
            if len(seen_ids) >= total:
                break

        logger.info(f"[{self.site_name}] Found {len(all_jobs)} jobs from Jibe API")
        return self.filter_by_title(all_jobs)
