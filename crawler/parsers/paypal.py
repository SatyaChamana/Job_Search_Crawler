import logging
from typing import List
from urllib.parse import urlparse, parse_qs

import requests

from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)

SEARCH_API = "https://paypal.eightfold.ai/api/pcsx/search"
JOB_URL_TEMPLATE = "https://paypal.eightfold.ai/careers/job/{position_id}"
PAGE_SIZE = 10
MAX_RESULTS = 200


class PayPalParser(ParserBase):
    """Parser for PayPal careers using eightfold PCSX search API.

    Uses displayJobId (e.g. R0135332) as the stable job_id for dedup,
    instead of the volatile eightfold position numeric ID.
    """

    def fetch_and_parse(self) -> List[JobPosting]:
        try:
            params = parse_qs(urlparse(self.url).query)
            query = params.get("query", ["software"])[0]
            location = params.get("location", ["united states"])[0]
            sort_by = params.get("sort_by", ["timestamp"])[0]

            logger.info(f"[{self.site_name}] Searching PayPal PCSX API: query='{query}', location='{location}'")

            all_jobs = []
            seen_ids = set()
            start = 0

            while start < MAX_RESULTS:
                resp = requests.get(
                    SEARCH_API,
                    params={
                        "domain": "paypal.com",
                        "query": query,
                        "location": location,
                        "start": str(start),
                        "sort_by": sort_by,
                    },
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    },
                    timeout=30,
                )
                resp.raise_for_status()
                positions = resp.json().get("data", {}).get("positions", [])

                if not positions:
                    break

                for pos in positions:
                    display_id = pos.get("displayJobId") or pos.get("atsJobId") or ""
                    position_id = str(pos.get("id", ""))

                    job_id = display_id or position_id
                    if not job_id or job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    locations = pos.get("locations", [])
                    location_str = "; ".join(locations) if locations else ""

                    all_jobs.append(JobPosting(
                        job_id=job_id,
                        title=pos.get("name", ""),
                        location=location_str,
                        url=JOB_URL_TEMPLATE.format(position_id=position_id),
                        company="PayPal",
                        date_posted="",
                        requisition_id=display_id,
                    ))

                start += len(positions)

            logger.info(f"[{self.site_name}] Found {len(all_jobs)} jobs from PCSX API")
            return self.filter_by_title(all_jobs)

        except Exception as e:
            logger.error(f"[{self.site_name}] Failed to fetch PayPal jobs: {e}")
            return []
