import logging
from typing import List, Optional

from crawler.parser_base import JobPosting

logger = logging.getLogger(__name__)


def filter_by_keywords(jobs: List[JobPosting], keywords: Optional[List[str]] = None) -> List[JobPosting]:
    """Phase 2 placeholder: pass-through that returns all jobs unchanged.

    In Phase 2, this will fetch each job's description page and match
    against provided keywords, populating job.keyword_matches.
    """
    # Phase 2 logic (not yet implemented):
    # if not keywords:
    #     return jobs
    # for job in jobs:
    #     description = fetch_job_description(job.url)
    #     description_lower = description.lower()
    #     job.keyword_matches = [kw for kw in keywords if kw.lower() in description_lower]
    # return [job for job in jobs if job.keyword_matches]

    return jobs
