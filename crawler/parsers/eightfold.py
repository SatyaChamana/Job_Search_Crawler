import logging
from typing import List

from crawler.fetcher import fetch_json
from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)


class EightfoldParser(ParserBase):
    """Parser for companies using the Eightfold.ai job platform.

    Requires 'eightfold_domain' in site_config, e.g.:
        eightfold_domain: aexp.eightfold.ai
        eightfold_company_domain: aexp.com
    """

    def fetch_and_parse(self) -> List[JobPosting]:
        ef_domain = self.site_config.get("eightfold_domain", "")
        if not ef_domain:
            logger.error(f"[{self.site_name}] No eightfold_domain configured")
            return []

        try:
            logger.info(f"[{self.site_name}] Fetching jobs from Eightfold API...")
            jobs = self._fetch_eightfold(ef_domain)
            logger.info(f"[{self.site_name}] Eightfold API returned {len(jobs)} jobs")
            return self.filter_by_title(jobs)
        except Exception as e:
            logger.error(f"[{self.site_name}] Eightfold API failed: {e}")
            return []

    def _fetch_eightfold(self, ef_domain: str) -> List[JobPosting]:
        company_domain = self.site_config.get("eightfold_company_domain", "")
        search_query = self.site_config.get("search_text", "Software")
        location = self.site_config.get("search_location", "United States")
        num = self.site_config.get("limit", 20)

        api_url = f"https://{ef_domain}/api/apply/v2/jobs"
        params = {
            "domain": company_domain,
            "query": search_query,
            "location": location,
            "num": num,
            "start": 0,
        }

        data = fetch_json(api_url, params=params)
        positions = data.get("positions", [])
        jobs = []

        for item in positions:
            job_id = str(item.get("id", item.get("ats_job_id", "")))
            name = item.get("name", item.get("posting_name", ""))
            location_str = item.get("location", "")
            if isinstance(location_str, dict):
                location_str = location_str.get("name", str(location_str))
            display_id = str(item.get("display_job_id", item.get("ats_job_id", "")))
            t_update = item.get("t_update", "")

            # Build URL
            canonical = item.get("canonical_url", "")
            if canonical:
                job_url = canonical
            else:
                job_url = f"https://{ef_domain}/careers?pid={job_id}&domain={company_domain}"

            jobs.append(JobPosting(
                job_id=job_id,
                title=name,
                location=location_str,
                url=job_url,
                company=self.site_name,
                date_posted=str(t_update),
                requisition_id=display_id,
            ))

        return jobs
