"""API endpoints for resume/cover letter generation."""

import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.database import supabase
from backend.services.document_generator import generate_document, MASTER_RESUME_FILE
from backend.services import supabase_storage

logger = logging.getLogger(__name__)

router = APIRouter()


class GenerateResponse(BaseModel):
    download_url: str
    cached: bool


class GenerationStatus(BaseModel):
    resume: dict | None = None
    cover_letter: dict | None = None


class MasterResumeBody(BaseModel):
    content: str


class BulkGenerateRequest(BaseModel):
    job_ids: List[int]
    doc_types: List[str] = ["resume", "cover_letter"]


class BulkJobResult(BaseModel):
    job_id: int
    doc_type: str
    success: bool
    download_url: str | None = None
    cached: bool = False
    error: str | None = None


class BulkGenerateResponse(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: List[BulkJobResult]


@router.post("/generate/resume/{job_id}", response_model=GenerateResponse)
def generate_resume(job_id: int):
    """Generate a tailored resume for a job posting."""
    try:
        result = generate_document(job_id, "resume")
        return GenerateResponse(**result)
    except Exception as e:
        logger.error(f"Resume generation failed for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/cover-letter/{job_id}", response_model=GenerateResponse)
def generate_cover_letter(job_id: int):
    """Generate a tailored cover letter for a job posting."""
    try:
        result = generate_document(job_id, "cover_letter")
        return GenerateResponse(**result)
    except Exception as e:
        logger.error(f"Cover letter generation failed for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/generate/status/{job_id}", response_model=GenerationStatus)
def generation_status(job_id: int):
    """Check what documents have been generated for a job."""
    result = (
        supabase.table("generated_documents")
        .select("doc_type, storage_path, created_at, llm_model")
        .eq("job_id", job_id)
        .execute()
    )
    status = GenerationStatus()
    for row in result.data:
        url = supabase_storage.get_signed_url(row["storage_path"])
        info = {"generated": True, "url": url, "created_at": row["created_at"], "model": row["llm_model"]}
        if row["doc_type"] == "resume":
            status.resume = info
        elif row["doc_type"] == "cover_letter":
            status.cover_letter = info
    return status


@router.put("/master-resume")
def update_master_resume(body: MasterResumeBody):
    """Upload or update the master resume."""
    content = body.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Resume content cannot be empty")

    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

    # Check if identical content already exists
    existing = (
        supabase.table("master_resume")
        .select("id")
        .eq("content_hash", content_hash)
        .limit(1)
        .execute()
    )
    if existing.data:
        return {"message": "Master resume unchanged", "content_hash": content_hash}

    supabase.table("master_resume").insert({
        "content": content,
        "content_hash": content_hash,
    }).execute()

    return {"message": "Master resume updated", "content_hash": content_hash}


@router.get("/master-resume")
def get_master_resume():
    """Get the current master resume. Checks Supabase first, falls back to master_resume.md."""
    # Try Supabase first
    try:
        result = (
            supabase.table("master_resume")
            .select("content, content_hash, updated_at")
            .order("updated_at", desc=True)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]
    except Exception:
        pass

    # Fall back to file
    if MASTER_RESUME_FILE.exists():
        content = MASTER_RESUME_FILE.read_text()
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return {"content": content, "content_hash": content_hash, "updated_at": None}

    raise HTTPException(status_code=404, detail="No master resume found")


class ManualDescriptionBody(BaseModel):
    description: str


@router.put("/jobs/{job_id}/description")
def set_job_description(job_id: int, body: ManualDescriptionBody):
    """Manually set a job description (for sites that block scraping)."""
    desc = body.description.strip()
    if not desc:
        raise HTTPException(status_code=400, detail="Description cannot be empty")
    supabase.table("jobs").update({"description": desc}).eq("id", job_id).execute()
    return {"message": "Description saved", "job_id": job_id}


@router.get("/jobs/{job_id}/description")
def get_job_description(job_id: int):
    """Get the cached description for a job."""
    result = supabase.table("jobs").select("description").eq("id", job_id).single().execute()
    return {"description": result.data.get("description") or ""}


@router.post("/bulk-generate", response_model=BulkGenerateResponse)
def bulk_generate(body: BulkGenerateRequest):
    """Generate documents for multiple jobs in parallel. Designed for n8n webhook integration."""
    if not body.job_ids:
        raise HTTPException(status_code=400, detail="job_ids cannot be empty")
    for dt in body.doc_types:
        if dt not in ("resume", "cover_letter"):
            raise HTTPException(status_code=400, detail=f"Invalid doc_type: {dt}")

    results: list[BulkJobResult] = []
    tasks = [(jid, dt) for jid in body.job_ids for dt in body.doc_types]

    def _run(job_id: int, doc_type: str) -> BulkJobResult:
        try:
            res = generate_document(job_id, doc_type)
            return BulkJobResult(
                job_id=job_id, doc_type=doc_type, success=True,
                download_url=res["download_url"], cached=res["cached"],
            )
        except Exception as e:
            logger.error(f"Bulk generate failed: job={job_id} type={doc_type}: {e}")
            return BulkJobResult(
                job_id=job_id, doc_type=doc_type, success=False, error=str(e),
            )

    max_workers = min(len(tasks), 4)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_run, jid, dt): (jid, dt) for jid, dt in tasks}
        for future in as_completed(futures):
            results.append(future.result())

    succeeded = sum(1 for r in results if r.success)
    return BulkGenerateResponse(
        total=len(results), succeeded=succeeded,
        failed=len(results) - succeeded, results=results,
    )
