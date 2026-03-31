import logging
from typing import List
from urllib.parse import urlparse, parse_qs

import requests

from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)

PAGE_DATA_URL = "https://www.databricks.com/careers-assets/page-data/company/careers/open-positions/page-data.json"

# Maps the URL location param regions to city substrings in office names
REGION_CITIES = {
    "West Coast - United States": [
        "San Francisco", "Mountain View", "Seattle", "Bellevue",
        "Remote - California", "Remote - Washington", "Remote - Arizona",
        "Remote - Oregon", "Los Angeles",
    ],
    "Northeast - United States": [
        "New York", "Boston", "New Jersey", "Philadelphia",
        "Remote - New York", "Remote - Massachusetts", "Connecticut",
        "Remote - New Jersey",
    ],
    "Central - United States": [
        "Chicago", "Denver", "Dallas", "Illinois", "Colorado",
        "Remote - Illinois", "Remote - Colorado", "Remote - Texas",
    ],
    "Southeast - United States": [
        "Atlanta", "Florida", "North Carolina", "Virginia",
        "Remote - Georgia", "Remote - Florida",
    ],
    "South - United States": [
        "Nashville", "Remote - Tennessee",
    ],
    "Southwest - United States": [
        "Austin", "Houston", "Remote - Texas",
    ],
}


class DatabricksParser(ParserBase):
    """Parser for Databricks careers using Gatsby static page-data.json (Greenhouse)."""

    def fetch_and_parse(self) -> List[JobPosting]:
        try:
            logger.info(f"[{self.site_name}] Fetching Databricks page data...")
            resp = requests.get(
                PAGE_DATA_URL,
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()

            nodes = (
                data.get("result", {})
                .get("pageContext", {})
                .get("data", {})
                .get("allGreenhouseJob", {})
                .get("nodes", [])
            )
            logger.info(f"[{self.site_name}] Total jobs in page data: {len(nodes)}")

            departments = self._parse_departments()
            location_region = self._parse_location()
            city_keywords = self._resolve_city_keywords(location_region)

            jobs = []
            for node in nodes:
                if not self._matches_department(node, departments):
                    continue
                if city_keywords and not self._matches_location(node, city_keywords):
                    continue

                offices = [o.get("name", "") for o in node.get("offices", [])]
                location = "; ".join(offices) if offices else node.get("location", {}).get("name", "")

                gh_id = str(node.get("gh_Id", ""))
                jobs.append(JobPosting(
                    job_id=gh_id,
                    title=node.get("title", ""),
                    location=location,
                    url=node.get("absolute_url", ""),
                    company="Databricks",
                    date_posted=node.get("updated_at", ""),
                ))

            logger.info(f"[{self.site_name}] {len(jobs)} jobs after dept/location filter")
            return self.filter_by_title(jobs)

        except Exception as e:
            logger.error(f"[{self.site_name}] Failed to parse Databricks careers: {e}")
            return []

    def _parse_departments(self) -> List[str]:
        params = parse_qs(urlparse(self.url).query)
        return params.get("department", [])

    def _parse_location(self) -> str:
        params = parse_qs(urlparse(self.url).query)
        locations = params.get("location", [])
        return locations[0] if locations else ""

    def _resolve_city_keywords(self, region: str) -> List[str]:
        if not region:
            return []
        if region in REGION_CITIES:
            return REGION_CITIES[region]
        # If location is "United States", match all US offices
        if "United States" in region:
            all_cities = []
            for cities in REGION_CITIES.values():
                all_cities.extend(cities)
            return all_cities
        # Treat as a direct city/keyword search
        return [region]

    def _matches_department(self, node: dict, departments: List[str]) -> bool:
        if not departments:
            return True
        job_depts = [d.get("name", "") for d in node.get("departments", [])]
        return any(dept in job_depts for dept in departments)

    def _matches_location(self, node: dict, city_keywords: List[str]) -> bool:
        offices = [o.get("name", "") for o in node.get("offices", [])]
        office_str = "; ".join(offices)
        return any(kw in office_str for kw in city_keywords)
