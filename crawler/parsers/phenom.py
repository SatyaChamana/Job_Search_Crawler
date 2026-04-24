import json
import logging
from typing import List
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import requests

from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)

DEFAULT_MAX_RESULTS = 30
PAGE_SIZE = 10


class PhenomParser(ParserBase):
    """Parser for Phenom-powered career sites (Abbott, Qualtrics, etc.).

    Phenom embeds job data in window.phApp.ddo.eagerLoadRefineSearch
    in the static HTML — no browser rendering needed.
    """

    def fetch_and_parse(self) -> List[JobPosting]:
        try:
            company = self.site_name
            logger.info(f"[{company}] Fetching Phenom careers page...")

            max_results = self.site_config.get("limit", DEFAULT_MAX_RESULTS)
            all_jobs = []
            seen_ids = set()
            offset = 0
            total_hits = None

            while offset < max_results:
                page_url = self._build_url(offset)
                logger.info(f"[{company}] Fetching from={offset}...")

                resp = requests.get(
                    page_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    },
                    timeout=30,
                )
                resp.raise_for_status()

                data = self._extract_phenom_data(resp.text)
                if data is None:
                    logger.warning(f"[{company}] Could not extract phApp.ddo at from={offset}")
                    break

                if total_hits is None:
                    total_hits = data.get("totalHits", 0)
                    logger.info(f"[{company}] Total hits: {total_hits}")

                jobs = data.get("data", {}).get("jobs", [])
                if not jobs:
                    break

                for j in jobs:
                    req_id = str(j.get("reqId") or j.get("jobId") or "")
                    if not req_id or req_id in seen_ids:
                        continue
                    seen_ids.add(req_id)

                    all_jobs.append(JobPosting(
                        job_id=req_id,
                        title=j.get("title", ""),
                        location=j.get("cityStateCountry", "") or j.get("location", ""),
                        url=j.get("jobUrl", ""),
                        company=company,
                        date_posted=j.get("postedDate", "")[:10] if j.get("postedDate") else "",
                        requisition_id=req_id,
                    ))

                offset += len(jobs)
                if total_hits and offset >= total_hits:
                    break

            logger.info(f"[{company}] Found {len(all_jobs)} jobs total")
            return self.filter_by_title(all_jobs)

        except Exception as e:
            logger.error(f"[{self.site_name}] Failed to parse Phenom careers: {e}")
            return []

    @staticmethod
    def _extract_phenom_data(html: str) -> dict | None:
        """Extract eagerLoadRefineSearch JSON from static HTML."""
        marker = "eagerLoadRefineSearch"
        idx = html.find(marker)
        if idx == -1:
            return None

        start = html.index("{", idx)
        depth = 0
        for i in range(start, min(start + 200000, len(html))):
            if html[i] == "{":
                depth += 1
            elif html[i] == "}":
                depth -= 1
            if depth == 0:
                return json.loads(html[start:i + 1])
        return None

    def _build_url(self, offset: int) -> str:
        parsed = urlparse(self.url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        params["from"] = [str(offset)]
        new_query = urlencode(params, doseq=True)
        return urlunparse(parsed._replace(query=new_query))
