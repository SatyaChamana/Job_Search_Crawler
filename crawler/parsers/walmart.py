import logging
from typing import List

import requests

from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)

API_URL = "https://careers.walmart.com/api/talent/job"
JOB_URL_TEMPLATE = "https://careers.walmart.com/us/en/jobs/{job_id}"
PAGE_SIZE = 20
MAX_PAGES = 15

SEARCH_QUERY = """
query JobSearch($jobSearchRequest: JobSearchRequest!) {
    jobSearch(jobSearchRequest: $jobSearchRequest) {
        searchResults {
            jobId
            jobTitle
            brand
            location {
                storeName
            }
        }
        totalResults
    }
}
"""

DEFAULT_POPULATIONS = [
    "WALMART_EXT_CAMPUS_US",
    "WALMART_EXT_FIELD_US",
    "SAMS_EXT_CAMPUS_US",
    "SAMS_EXT_FIELD_US",
    "VIZIO_CAMPUS_EXTERNAL",
    "VIZIO_FIELD_EXTERNAL",
]


class WalmartParser(ParserBase):
    """Parser for Walmart careers using their GraphQL API."""

    def fetch_and_parse(self) -> List[JobPosting]:
        search_text = self.site_config.get("search_text", "software")
        limit = self.site_config.get("limit", PAGE_SIZE)
        populations = self.site_config.get("populations", DEFAULT_POPULATIONS)

        logger.info(f"[{self.site_name}] Searching Walmart GraphQL API: '{search_text}'")

        all_jobs = []
        seen_ids = set()
        offset = 0

        for _ in range(MAX_PAGES):
            payload = {
                "query": SEARCH_QUERY,
                "variables": {
                    "jobSearchRequest": {
                        "searchString": search_text,
                        "isTitleSearch": False,
                        "population": populations,
                        "from": offset,
                        "size": limit,
                        "sortBy": None,
                        "filters": None,
                    }
                },
            }

            resp = requests.post(
                API_URL,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                },
                timeout=30,
            )
            resp.raise_for_status()

            data = resp.json().get("data", {}).get("jobSearch", {})
            results = data.get("searchResults", [])
            total = data.get("totalResults", 0)

            if not results:
                break

            for r in results:
                job_id = r.get("jobId", "")
                if not job_id or job_id in seen_ids:
                    continue
                seen_ids.add(job_id)

                location_info = r.get("location") or []
                if isinstance(location_info, list):
                    location = "; ".join(
                        loc.get("storeName", "") for loc in location_info if loc.get("storeName")
                    )
                elif isinstance(location_info, dict):
                    location = location_info.get("storeName", "")
                else:
                    location = ""
                brand = r.get("brand", "Walmart")

                all_jobs.append(JobPosting(
                    job_id=job_id,
                    title=r.get("jobTitle", ""),
                    location=location,
                    url=JOB_URL_TEMPLATE.format(job_id=job_id),
                    company=brand or "Walmart",
                ))

            offset += limit
            if offset >= total:
                break

        logger.info(f"[{self.site_name}] Found {len(all_jobs)} jobs from Walmart API")
        return self.filter_by_title(all_jobs)
