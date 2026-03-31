import logging
from typing import List

from crawler.fetcher import fetch_page
from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)


class WorkdayParser(ParserBase):
    """Parser for companies using the Workday job platform API.

    Requires 'workday_url' in site_config, e.g.:
        workday_url: "https://adobe.wd5.myworkdayjobs.com/wday/cxs/adobe/external_experienced/jobs"
    """

    def fetch_and_parse(self) -> List[JobPosting]:
        workday_url = self.site_config.get("workday_url", "")
        if not workday_url:
            logger.error(f"[{self.site_name}] No workday_url configured")
            return []

        try:
            logger.info(f"[{self.site_name}] Fetching jobs from Workday API...")
            jobs = self._fetch_workday(workday_url)
            logger.info(f"[{self.site_name}] Workday API returned {len(jobs)} jobs")
            return self.filter_by_title(jobs)
        except Exception as e:
            logger.error(f"[{self.site_name}] Workday API failed: {e}")
            return []

    def _fetch_workday(self, api_url: str) -> List[JobPosting]:
        import requests

        search_text = self.site_config.get("search_text", "Software")
        limit = self.site_config.get("limit", 20)

        response = requests.post(
            api_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json={
                "appliedFacets": self.site_config.get("applied_facets", {}),
                "limit": limit,
                "offset": 0,
                "searchText": search_text,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        # Convert API URL to public URL: strip /wday/cxs/{company} from the path
        # e.g. https://co.wd1.myworkdayjobs.com/wday/cxs/co/Ext/jobs -> https://co.wd1.myworkdayjobs.com/Ext
        import re
        base_url = re.sub(r"/wday/cxs/[^/]+", "", api_url.rsplit("/jobs", 1)[0])
        postings = data.get("jobPostings", [])
        jobs = []

        for item in postings:
            title = item.get("title", "")
            external_path = item.get("externalPath", "")
            location = item.get("locationsText", "")
            posted_on = item.get("postedOn", "")
            bullet_fields = item.get("bulletFields", [])
            requisition_id = bullet_fields[0] if bullet_fields else ""

            job_url = f"{base_url}{external_path}" if external_path else ""

            # Extract job ID from path (e.g., /job/San-Jose/Title_R158008 -> R158008)
            job_id = requisition_id or external_path.rstrip("/").split("_")[-1] if external_path else ""

            jobs.append(JobPosting(
                job_id=job_id,
                title=title,
                location=location,
                url=job_url,
                company=self.site_name,
                date_posted=posted_on,
                requisition_id=requisition_id,
            ))

        return jobs
