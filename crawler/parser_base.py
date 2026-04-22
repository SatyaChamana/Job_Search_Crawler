from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List


@dataclass
class JobPosting:
    job_id: str
    title: str
    location: str
    url: str
    company: str
    date_posted: str = ""
    requisition_id: str = ""
    keyword_matches: List[str] = field(default_factory=list)  # Phase 2 field

    @property
    def dedup_key(self) -> str:
        return f"{self.title.strip().lower()}|{self.job_id.strip().lower()}"


@dataclass
class CrawlSiteResult:
    label: str           # "Adobe (Software)"
    site_name: str       # "Adobe"
    search_text: str     # "Software"
    parser_name: str     # "workday"
    success: bool
    error_message: str = ""
    jobs_found: int = 0
    new_jobs_added: int = 0


class ParserBase(ABC):
    def __init__(self, site_config: dict):
        self.site_config = site_config
        self.site_name = site_config.get("name", "Unknown")
        self.url = site_config.get("url", "")
        self.target_titles = site_config.get("target_titles", [])

    @abstractmethod
    def fetch_and_parse(self) -> List[JobPosting]:
        pass

    def filter_by_title(self, jobs: List[JobPosting]) -> List[JobPosting]:
        """Filter jobs by case-insensitive substring match against target_titles,
        then exclude jobs matching exclude_titles."""
        if not self.target_titles:
            return jobs
        filtered = []
        for job in jobs:
            job_title_lower = job.title.lower()
            for target in self.target_titles:
                if target.lower() in job_title_lower:
                    filtered.append(job)
                    break
        exclude_titles = self.site_config.get("exclude_titles", [])
        if exclude_titles:
            filtered = [j for j in filtered if not any(ex.lower() in j.title.lower() for ex in exclude_titles)]
        return filtered
