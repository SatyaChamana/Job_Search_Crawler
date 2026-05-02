import math
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Query

from backend.database import supabase
from backend.models import JobListResponse, JobResponse, StatsResponse

router = APIRouter()


@router.get("/jobs", response_model=JobListResponse)
def list_jobs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    company: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query("added_on", pattern="^(added_on|title|company|date_posted)$"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
):
    # Build query
    query = supabase.table("jobs").select("*", count="exact")

    if company:
        query = query.ilike("company", f"%{company}%")
    if search:
        query = query.or_(f"title.ilike.%{search}%,company.ilike.%{search}%,location.ilike.%{search}%")

    # Sort
    ascending = sort_dir == "asc"
    query = query.order(sort_by, desc=not ascending)

    # Paginate
    offset = (page - 1) * per_page
    query = query.range(offset, offset + per_page - 1)

    result = query.execute()
    total = result.count or 0

    return JobListResponse(
        jobs=[JobResponse(**row) for row in result.data],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 1,
    )


@router.get("/jobs/{job_db_id}", response_model=JobResponse)
def get_job(job_db_id: int):
    result = supabase.table("jobs").select("*").eq("id", job_db_id).single().execute()
    return JobResponse(**result.data)


@router.get("/stats", response_model=StatsResponse)
def get_stats():
    # Total jobs
    total_result = supabase.table("jobs").select("id", count="exact").execute()
    total_jobs = total_result.count or 0

    # Distinct companies
    companies_result = supabase.table("jobs").select("company").execute()
    companies = {row["company"] for row in companies_result.data}

    # Jobs added today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    today_result = (
        supabase.table("jobs")
        .select("id", count="exact")
        .gte("added_on", today_start)
        .execute()
    )
    jobs_today = today_result.count or 0

    return StatsResponse(
        total_jobs=total_jobs,
        companies_count=len(companies),
        jobs_added_today=jobs_today,
    )
