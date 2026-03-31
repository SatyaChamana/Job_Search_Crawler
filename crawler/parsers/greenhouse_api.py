import logging
from typing import List

import requests

from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)

API_URL = "https://boards-api.greenhouse.io/v1/boards/{board}/jobs"


class GreenhouseAPIParser(ParserBase):
    """Parser for sites using the public Greenhouse boards API.

    Config keys:
        greenhouse_board: Board name (e.g. "cloudflare")
    """

    def fetch_and_parse(self) -> List[JobPosting]:
        board = self.site_config.get("greenhouse_board", "")
        if not board:
            logger.error(f"[{self.site_name}] No greenhouse_board configured")
            return []

        url = API_URL.format(board=board)
        logger.info(f"[{self.site_name}] Fetching jobs from Greenhouse API: {board}")

        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        jobs_list = data.get("jobs", [])

        all_jobs = []
        for j in jobs_list:
            job_id = str(j.get("id", ""))
            if not job_id:
                continue

            location = j.get("location", {}).get("name", "")

            all_jobs.append(JobPosting(
                job_id=job_id,
                title=j.get("title", ""),
                location=location,
                url=j.get("absolute_url", ""),
                company=self.site_name,
                date_posted=j.get("updated_at", "")[:10] if j.get("updated_at") else "",
            ))

        logger.info(f"[{self.site_name}] Found {len(all_jobs)} jobs from Greenhouse API")
        return self.filter_by_title(all_jobs)
