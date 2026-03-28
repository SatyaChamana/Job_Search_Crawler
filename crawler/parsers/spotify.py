import logging
from typing import List

from crawler.fetcher import fetch_json
from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)

SPOTIFY_API_URL = "https://api.lifeatspotify.com/wp-json/animal/v1/job/search"


class SpotifyParser(ParserBase):
    """Parser for Spotify using their public jobs API."""

    def fetch_and_parse(self) -> List[JobPosting]:
        try:
            logger.info(f"[{self.site_name}] Fetching from Spotify API...")
            jobs = self._fetch_api()
            logger.info(f"[{self.site_name}] API returned {len(jobs)} jobs")
            return self.filter_by_title(jobs)
        except Exception as e:
            logger.error(f"[{self.site_name}] Spotify API failed: {e}")
            return []

    def _fetch_api(self) -> List[JobPosting]:
        # Build category filter from site config URL params
        categories = self.site_config.get("categories", "backend,data,machine-learning,mobile,security,web")
        location = self.site_config.get("search_location", "usa")

        params = {"c": categories, "l": location}
        data = fetch_json(SPOTIFY_API_URL, params=params)

        results = data.get("result", [])
        jobs = []

        for item in results:
            job_id = item.get("id", "")
            title = item.get("text", "")

            locations = item.get("locations", [])
            location_str = ", ".join(
                loc.get("location", "") for loc in locations
            ) if locations else ""

            category = item.get("sub_category", {}).get("name", "")
            job_url = f"https://www.lifeatspotify.com/jobs/{job_id}"

            jobs.append(JobPosting(
                job_id=job_id,
                title=title,
                location=location_str,
                url=job_url,
                company="Spotify",
            ))

        return jobs
