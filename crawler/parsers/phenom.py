import logging
from typing import List
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)

MAX_PAGES = 20
PAGE_SIZE = 10


class PhenomParser(ParserBase):
    """Parser for Phenom-powered career sites (e.g. Abbott).

    Phenom embeds job data in window.phApp.ddo.eagerLoadRefineSearch on
    initial page load. Filters (country, sort) are passed as URL query
    params. Pagination uses the ``from`` param.
    """

    def fetch_and_parse(self) -> List[JobPosting]:
        from crawler.browser import fetch_rendered_html
        from playwright.sync_api import sync_playwright
        import json

        try:
            company = self.site_name
            wait_ms = self.site_config.get("wait_ms", 8000)

            logger.info(f"[{company}] Fetching Phenom careers page...")

            all_jobs = []
            seen_ids = set()

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                offset = 0
                total_hits = None

                while offset < MAX_PAGES * PAGE_SIZE:
                    page_url = self._build_url(offset)
                    logger.info(f"[{company}] Loading page from={offset}...")
                    page.goto(page_url, wait_until="domcontentloaded")
                    page.wait_for_timeout(wait_ms)

                    try:
                        raw = page.evaluate(
                            "() => JSON.stringify(window.phApp.ddo.eagerLoadRefineSearch)"
                        )
                        data = json.loads(raw)
                    except Exception:
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

                browser.close()

            logger.info(f"[{company}] Found {len(all_jobs)} jobs total")
            return self.filter_by_title(all_jobs)

        except Exception as e:
            logger.error(f"[{self.site_name}] Failed to parse Phenom careers: {e}")
            return []

    def _build_url(self, offset: int) -> str:
        parsed = urlparse(self.url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        params["from"] = [str(offset)]
        new_query = urlencode(params, doseq=True)
        return urlunparse(parsed._replace(query=new_query))
