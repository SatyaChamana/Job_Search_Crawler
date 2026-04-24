import logging
from typing import List

import requests

from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)

AMAZON_SEARCH_URL = "https://www.amazon.jobs/en/search.json"


class AmazonParser(ParserBase):
    """Parser for Amazon careers via their public JSON search API."""

    def fetch_and_parse(self) -> List[JobPosting]:
        try:
            logger.info(f"[{self.site_name}] Fetching from Amazon Jobs API...")
            jobs = self._fetch_api()
            logger.info(f"[{self.site_name}] API returned {len(jobs)} jobs")
            return self.filter_by_title(jobs)
        except Exception as e:
            logger.error(f"[{self.site_name}] Amazon API failed: {e}")
            return []

    def _fetch_api(self) -> List[JobPosting]:
        search_text = self.site_config.get("search_text", "software engineer")
        location = self.site_config.get("search_location", "United States")
        limit = self.site_config.get("limit", 20)

        params = {
            "base_query": search_text,
            "loc_query": location,
            "offset": 0,
            "result_limit": limit,
            "sort": "recent",
        }

        resp = requests.get(
            AMAZON_SEARCH_URL,
            params=params,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json",
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        job_list = data.get("jobs", [])
        jobs = []

        for item in job_list:
            job_id = item.get("id_icims", item.get("id", ""))
            title = item.get("title", "")
            city = item.get("city", "")
            state = item.get("state", "")
            country = item.get("country_code", "")
            location_str = ", ".join(filter(None, [city, state, country]))
            posted = item.get("posted_date", "")
            job_path = item.get("job_path", "")

            job_url = f"https://www.amazon.jobs{job_path}" if job_path else ""

            jobs.append(JobPosting(
                job_id=str(job_id),
                title=title,
                location=location_str,
                url=job_url,
                company=self.site_name,
                date_posted=posted,
            ))

        return jobs
