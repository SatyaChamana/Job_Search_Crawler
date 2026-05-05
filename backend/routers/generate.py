"""API endpoints for resume/cover letter generation."""

import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from backend.database import supabase
from backend.services.document_generator import generate_document, MASTER_RESUME_MD

logger = logging.getLogger(__name__)

router = APIRouter()


class LLMProviderBody(BaseModel):
    provider: str


@router.get("/llm-provider")
def get_llm_provider():
    """Get the active LLM provider."""
    from backend.config import settings
    return {
        "provider": settings.llm_provider,
        "nvidia_model": settings.nvidia_model,
        "ollama_model": settings.ollama_model,
    }


@router.put("/llm-provider")
def set_llm_provider(body: LLMProviderBody):
    """Switch between 'nvidia' and 'ollama'."""
    from backend.config import settings
    if body.provider not in ("nvidia", "ollama", "anthropic"):
        raise HTTPException(status_code=400, detail="Provider must be 'nvidia', 'ollama', or 'anthropic'")
    settings.llm_provider = body.provider
    return {"provider": settings.llm_provider}


class MasterResumeBody(BaseModel):
    content: str


@router.post("/generate/resume/{job_id}")
def generate_resume(job_id: int):
    """Generate a tailored resume and return the docx directly."""
    try:
        file_bytes, filename = generate_document(job_id, "resume")
        media_type = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            if filename.endswith(".docx")
            else "application/pdf"
        )
        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        logger.error(f"Resume generation failed for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/cover-letter/{job_id}")
def generate_cover_letter(job_id: int):
    """Generate a tailored cover letter and return the PDF directly."""
    try:
        pdf_bytes, filename = generate_document(job_id, "cover_letter")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        logger.error(f"Cover letter generation failed for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/master-resume")
def update_master_resume(body: MasterResumeBody):
    """Upload or update the master resume."""
    content = body.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Resume content cannot be empty")

    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

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

    if MASTER_RESUME_MD.exists():
        content = MASTER_RESUME_MD.read_text()
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


@router.post("/jobs/{job_id}/fetch-description")
def fetch_job_description(job_id: int):
    """Scrape the job description from the job's URL and cache it."""
    from backend.services.job_scraper import scrape_job_description

    result = supabase.table("jobs").select("url, description").eq("id", job_id).single().execute()
    job = result.data
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        desc = scrape_job_description(job["url"])
        supabase.table("jobs").update({"description": desc}).eq("id", job_id).execute()
        return {"description": desc}
    except Exception as e:
        logger.error(f"Failed to fetch description for job {job_id}: {e}")
        raise HTTPException(status_code=502, detail=f"Could not scrape description: {e}")


class BulkGenerateRequest(BaseModel):
    job_ids: List[int]
    doc_types: List[str] = ["resume", "cover_letter"]


class BulkJobResult(BaseModel):
    job_id: int
    doc_type: str
    success: bool
    error: str | None = None


class BulkGenerateResponse(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: List[BulkJobResult]


@router.post("/bulk-generate", response_model=BulkGenerateResponse)
def bulk_generate(body: BulkGenerateRequest):
    """Generate documents for multiple jobs. PDFs are generated but not stored — use single endpoints to download."""
    if not body.job_ids:
        raise HTTPException(status_code=400, detail="job_ids cannot be empty")
    for dt in body.doc_types:
        if dt not in ("resume", "cover_letter"):
            raise HTTPException(status_code=400, detail=f"Invalid doc_type: {dt}")

    results: list[BulkJobResult] = []
    tasks = [(jid, dt) for jid in body.job_ids for dt in body.doc_types]

    def _run(job_id: int, doc_type: str) -> BulkJobResult:
        try:
            generate_document(job_id, doc_type)
            return BulkJobResult(job_id=job_id, doc_type=doc_type, success=True)
        except Exception as e:
            logger.error(f"Bulk generate failed: job={job_id} type={doc_type}: {e}")
            return BulkJobResult(job_id=job_id, doc_type=doc_type, success=False, error=str(e))

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
