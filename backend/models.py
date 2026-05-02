from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class JobResponse(BaseModel):
    id: int
    job_id: str
    requisition_id: str = ""
    title: str
    company: str
    location: str = ""
    date_posted: str = ""
    url: str
    added_on: datetime
    description: Optional[str] = None


class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int
    page: int
    per_page: int
    pages: int


class StatsResponse(BaseModel):
    total_jobs: int
    companies_count: int
    jobs_added_today: int
