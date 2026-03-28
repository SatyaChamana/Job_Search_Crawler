import re
import logging
from typing import List

from bs4 import BeautifulSoup

from crawler.browser import fetch_rendered_html
from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)


class OracleHCMParser(ParserBase):
    """Parser for career sites powered by Oracle HCM Cloud (JPMC, Oracle, etc.).

    These sites render job listings via JavaScript using a 'job-tile' class
    structure. Requires Playwright for browser rendering.
    """

    def fetch_and_parse(self) -> List[JobPosting]:
        try:
            logger.info(f"[{self.site_name}] Fetching with browser (Oracle HCM)...")
            wait_ms = self.site_config.get("wait_ms", 12000)
            html = fetch_rendered_html(self.url, wait_ms=wait_ms)
            jobs = self._parse_tiles(html)
            logger.info(f"[{self.site_name}] Found {len(jobs)} jobs")
            return self.filter_by_title(jobs)
        except Exception as e:
            logger.error(f"[{self.site_name}] Oracle HCM parsing failed: {e}")
            return []

    def _parse_tiles(self, html: str) -> List[JobPosting]:
        soup = BeautifulSoup(html, "html.parser")
        jobs = []
        seen_ids = set()

        tiles = soup.find_all(class_="job-tile")
        for tile in tiles:
            title_el = tile.find(class_="job-tile__title")
            sub_el = tile.find(class_="job-tile__subheader")
            link = tile.find("a", class_="job-grid-item__link")

            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue

            href = link.get("href", "") if link else ""

            # Extract job ID from URL
            m = re.search(r"/job/(\d+)", href)
            job_id = m.group(1) if m else ""

            if not job_id or job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            # Extract location from subheader
            # Format: "City, State, CountryDepartmentCategory" or
            # "LocationsUnited StatesHot JobTrending..."
            location = ""
            if sub_el:
                sub_text = sub_el.get_text(strip=True)
                # Clean Oracle-specific noise
                sub_text = re.sub(r"^Locations?", "", sub_text)
                sub_text = re.sub(r"Hot Job.*$", "", sub_text)
                sub_text = re.sub(r"Trending.*$", "", sub_text)
                # Split on known department/category keywords
                for delimiter in [
                    "Technology", "Software", "Engineering", "Cloud",
                    "Applications", "Operations", "Data", "Finance",
                    "Corporate", "Consumer", "Investment", "Commercial",
                    "Asset", "Global", "Digital", "Business",
                ]:
                    if delimiter in sub_text:
                        location = sub_text.split(delimiter)[0].strip()
                        break
                if not location:
                    location = sub_text.strip()

            jobs.append(JobPosting(
                job_id=job_id,
                title=title,
                location=location,
                url=href,
                company=self.site_name,
            ))

        return jobs
