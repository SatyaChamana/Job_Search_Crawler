import re
import logging
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler.fetcher import fetch_json, fetch_page
from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)

API_URL = "https://careers.salesforce.com/api/apply/v2/jobs"


class SalesforceParser(ParserBase):
    def fetch_and_parse(self) -> List[JobPosting]:
        """Try API first, fall back to HTML parsing."""
        try:
            logger.info(f"[{self.site_name}] Trying API...")
            jobs = self._try_api()
            if jobs:
                logger.info(f"[{self.site_name}] API returned {len(jobs)} jobs")
                return self.filter_by_title(jobs)
        except Exception as e:
            logger.warning(f"[{self.site_name}] API failed: {e}")

        try:
            logger.info(f"[{self.site_name}] Falling back to HTML parsing...")
            jobs = self._try_html()
            logger.info(f"[{self.site_name}] HTML parsing returned {len(jobs)} jobs")
            return self.filter_by_title(jobs)
        except Exception as e:
            logger.error(f"[{self.site_name}] HTML parsing also failed: {e}")
            return []

    def _try_api(self) -> List[JobPosting]:
        """Fetch jobs from the Salesforce careers API."""
        params = {
            "domain": "salesforce.com",
            "query": "Software",
            "location": "United States of America",
            "num": 20,
            "start": 0,
        }
        data = fetch_json(API_URL, params=params)
        return self._parse_api_response(data)

    def _parse_api_response(self, data: dict) -> List[JobPosting]:
        """Parse the API JSON response into JobPosting objects."""
        positions = data.get("positions") or data.get("results") or []
        jobs = []
        for item in positions:
            job_id = str(item.get("id", item.get("job_id", "")))
            title = item.get("name", item.get("title", ""))
            location = item.get("location", item.get("location_name", ""))
            if isinstance(location, dict):
                location = location.get("name", str(location))
            date_posted = item.get("created_at", item.get("date_posted", ""))
            requisition_id = str(item.get("requisition_id", item.get("req_id", "")))
            job_url = item.get("url", item.get("absolute_url", ""))
            if not job_url and job_id:
                job_url = f"https://careers.salesforce.com/en/jobs/{job_id}/"

            jobs.append(JobPosting(
                job_id=job_id,
                title=title,
                location=location,
                url=job_url,
                company="Salesforce",
                date_posted=date_posted,
                requisition_id=requisition_id,
            ))
        return jobs

    def _try_html(self) -> List[JobPosting]:
        """Fetch and parse the HTML careers page."""
        response = fetch_page(self.url)
        return self._parse_html(response.text)

    def _parse_html(self, html: str) -> List[JobPosting]:
        """Parse HTML to extract job postings."""
        soup = BeautifulSoup(html, "html.parser")
        jobs = []
        seen_ids = set()

        links = soup.find_all("a", href=re.compile(r"/en/jobs/"))
        for link in links:
            href = link.get("href", "")
            match = re.search(r"/en/jobs/([^/]+)", href)
            if not match:
                continue

            job_id = match.group(1)
            if job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            title = link.get_text(strip=True)
            if not title:
                continue

            job_url = urljoin("https://careers.salesforce.com", href)

            # Try to find location from parent card elements
            location = ""
            card = link.find_parent(["div", "li", "article"])
            if card:
                loc_el = card.find(
                    class_=re.compile(r"location|city|region", re.IGNORECASE)
                )
                if loc_el:
                    location = loc_el.get_text(strip=True)

            jobs.append(JobPosting(
                job_id=job_id,
                title=title,
                location=location,
                url=job_url,
                company="Salesforce",
            ))

        return jobs
