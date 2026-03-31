import logging
from typing import List
from urllib.parse import urlparse, parse_qs

import requests

from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)

API_URL = "https://www.uber.com/api/loadSearchJobsResults?localeCode=en"
JOB_URL_TEMPLATE = "https://www.uber.com/global/en/careers/list/{job_id}/"
MAX_PAGES = 10


class UberParser(ParserBase):
    """Parser for Uber careers using their internal search API."""

    def fetch_and_parse(self) -> List[JobPosting]:
        try:
            locations = self._parse_locations()
            query = self._parse_query()
            logger.info(f"[{self.site_name}] Searching Uber API: query='{query}', {len(locations)} locations")

            all_jobs = []
            seen_ids = set()
            page = 0

            while page < MAX_PAGES:
                payload = {
                    "limit": 20,
                    "page": page,
                    "params": {"query": query, "location": locations},
                }
                resp = requests.post(
                    API_URL,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                        "x-csrf-token": "x",
                    },
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json().get("data", {})
                results = data.get("results", [])

                if not results:
                    break

                for r in results:
                    job_id = str(r.get("id", ""))
                    if not job_id or job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    locs = r.get("allLocations", [])
                    location = "; ".join(
                        f"{l.get('city', '')}, {l.get('region', '')}"
                        for l in locs
                        if l.get("city")
                    ) or r.get("location", "")

                    all_jobs.append(JobPosting(
                        job_id=job_id,
                        title=r.get("title", ""),
                        location=location,
                        url=JOB_URL_TEMPLATE.format(job_id=job_id),
                        company="Uber",
                        date_posted=r.get("creationDate", ""),
                    ))

                total = data.get("totalResults", {}).get("low", 0)
                if len(seen_ids) >= total:
                    break
                page += 1

            logger.info(f"[{self.site_name}] Found {len(all_jobs)} jobs from API")
            return self.filter_by_title(all_jobs)

        except Exception as e:
            logger.error(f"[{self.site_name}] Failed to fetch Uber jobs: {e}")
            return []

    def _parse_query(self) -> str:
        params = parse_qs(urlparse(self.url).query)
        return params.get("query", ["Software"])[0]

    def _parse_locations(self) -> List[dict]:
        params = parse_qs(urlparse(self.url).query)
        locations = []
        for loc in params.get("location", []):
            parts = loc.split("-", 2)
            if len(parts) == 3:
                locations.append({"country": parts[0], "region": parts[1], "city": parts[2]})
            elif len(parts) == 2:
                locations.append({"country": parts[0], "region": parts[1]})
        return locations
