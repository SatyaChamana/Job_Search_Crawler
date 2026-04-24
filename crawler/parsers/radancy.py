import logging
from typing import List
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import requests
from bs4 import BeautifulSoup

from crawler.parser_base import ParserBase, JobPosting

logger = logging.getLogger(__name__)

MAX_PAGES = 20


class RadancyParser(ParserBase):
    """Parser for Radancy/TMP-powered career sites (Wells Fargo, Chime, etc.).

    Static HTML with .card.card-job elements and ?page= pagination.
    """

    def fetch_and_parse(self) -> List[JobPosting]:
        parsed = urlparse(self.url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        logger.info(f"[{self.site_name}] Fetching careers from {base_url}...")

        all_jobs = []
        seen_ids = set()

        for page in range(1, MAX_PAGES + 1):
            page_url = self._build_url(page)
            resp = requests.get(
                page_url,
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
                timeout=30,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Try classic .card.card-job layout, then section29, then generic a[data-job-id]
            cards = soup.select(".card.card-job")
            if cards:
                new_jobs = self._parse_card_layout(cards, base_url, seen_ids)
            else:
                items = soup.select("li.section29__search-results-li")
                if items:
                    new_jobs = self._parse_section29_layout(items, base_url, seen_ids)
                else:
                    job_links = soup.select("#search-results-list a[data-job-id]")
                    if not job_links:
                        break
                    new_jobs = self._parse_job_link_layout(job_links, base_url, seen_ids)

            if not new_jobs:
                break

            all_jobs.extend(new_jobs)
            logger.info(f"[{self.site_name}] Page {page}: {len(new_jobs)} jobs")

        logger.info(f"[{self.site_name}] Found {len(all_jobs)} jobs total")
        return self.filter_by_title(all_jobs)

    def _parse_card_layout(self, cards, base_url, seen_ids):
        """Parse classic .card.card-job layout (Wells Fargo, Chime)."""
        jobs = []
        for card in cards:
            title_el = card.select_one("h2.card-title a, h3.card-title a")
            if not title_el:
                continue

            id_el = card.select_one("[data-id]")
            job_id = id_el.get("data-id", "") if id_el else ""
            if not job_id or job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            title = title_el.get_text(strip=True)
            href = title_el.get("href", "")
            meta_items = card.select("ul.job-meta li.list-inline-item")
            location = ""
            date_posted = ""
            for item in meta_items:
                icon = item.select_one("svg use, i")
                icon_ref = (icon.get("xlink:href", "") or icon.get("class", "")) if icon else ""
                text = item.get_text(strip=True)
                if "map-marker" in icon_ref or "location" in icon_ref:
                    location = text
                elif "calendar" in icon_ref or "clock" in icon_ref:
                    date_posted = text
            if not location and meta_items:
                location = "; ".join(m.get_text(strip=True) for m in meta_items)

            jobs.append(JobPosting(
                job_id=job_id,
                title=title,
                location=location,
                url=f"{base_url}{href}" if href.startswith("/") else href,
                company=self.site_name,
                date_posted=date_posted,
            ))
        return jobs

    def _parse_section29_layout(self, items, base_url, seen_ids):
        """Parse section29 layout (Palo Alto Networks)."""
        jobs = []
        for item in items:
            link = item.select_one("a[data-job-id]")
            if not link:
                continue

            job_id = link.get("data-job-id", "")
            if not job_id or job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            title_el = link.select_one("h2")
            title = title_el.get_text(strip=True) if title_el else ""
            href = link.get("href", "")
            loc_el = link.select_one(".section29__result-location")
            location = loc_el.get_text(strip=True) if loc_el else ""

            jobs.append(JobPosting(
                job_id=job_id,
                title=title,
                location=location,
                url=f"{base_url}{href}" if href.startswith("/") else href,
                company=self.site_name,
            ))
        return jobs

    def _parse_job_link_layout(self, job_links, base_url, seen_ids):
        """Parse generic a[data-job-id] layout (Disney, NetApp)."""
        jobs = []
        for link in job_links:
            job_id = link.get("data-job-id", "")
            if not job_id or job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            title_el = link.select_one("h2") or link.select_one("h3")
            title = title_el.get_text(strip=True) if title_el else ""
            href = link.get("href", "")
            loc_el = link.select_one(".job-location")
            location = loc_el.get_text(strip=True) if loc_el else ""
            date_el = link.select_one(".job-date-posted")
            date_posted = date_el.get_text(strip=True) if date_el else ""

            jobs.append(JobPosting(
                job_id=job_id,
                title=title,
                location=location,
                url=f"{base_url}{href}" if href.startswith("/") else href,
                company=self.site_name,
                date_posted=date_posted,
            ))
        return jobs

    def _build_url(self, page: int) -> str:
        parsed = urlparse(self.url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        # Radancy sites use ?page= (Wells Fargo, Chime) or &p= (Palo Alto)
        page_key = "p" if "/search-jobs/" in parsed.path else "page"
        params[page_key] = [str(page)]
        new_query = urlencode(params, doseq=True)
        return urlunparse(parsed._replace(query=new_query))
