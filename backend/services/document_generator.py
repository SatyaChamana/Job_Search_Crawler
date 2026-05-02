"""Orchestrator: scrape job description -> LLM generate -> PDF -> upload."""

import hashlib
import logging
import os
from pathlib import Path

from fpdf import FPDF

from backend.database import supabase
from backend.services.job_scraper import scrape_job_description
from backend.services.llm_client import generate_text
from backend.services import supabase_storage

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def _load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.txt"
    return path.read_text()


MASTER_RESUME_FILE = Path(__file__).parent.parent.parent / "master_resume.md"


def _load_master_resume() -> tuple[str, str]:
    """Load master resume. Checks Supabase first, falls back to master_resume.md file."""
    # Try Supabase first (UI-uploaded resume takes priority)
    try:
        result = (
            supabase.table("master_resume")
            .select("content, content_hash")
            .order("updated_at", desc=True)
            .limit(1)
            .execute()
        )
        if result.data:
            row = result.data[0]
            return row["content"], row["content_hash"]
    except Exception:
        pass  # Supabase not configured or unreachable — fall back to file

    # Fall back to master_resume.md file
    if MASTER_RESUME_FILE.exists():
        content = MASTER_RESUME_FILE.read_text()
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return content, content_hash

    raise RuntimeError(
        "No master resume found. Either place master_resume.md in the project root "
        "or upload via PUT /api/master-resume."
    )


def _get_job(job_id: int) -> dict:
    """Fetch job from Supabase by database ID."""
    result = supabase.table("jobs").select("*").eq("id", job_id).single().execute()
    return result.data


def _get_description(job: dict) -> str:
    """Get job description: use cached if available, otherwise scrape and cache."""
    if job.get("description"):
        return job["description"]

    desc = scrape_job_description(job["url"])
    # Cache it
    supabase.table("jobs").update({"description": desc}).eq("id", job["id"]).execute()
    return desc


def _check_cache(job_id: int, doc_type: str, prompt_hash: str) -> dict | None:
    """Check if a document already exists with the same prompt hash."""
    result = (
        supabase.table("generated_documents")
        .select("*")
        .eq("job_id", job_id)
        .eq("doc_type", doc_type)
        .eq("prompt_hash", prompt_hash)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def _text_to_pdf(text: str) -> bytes:
    """Convert plain text to a PDF and return the bytes."""
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)

    for line in text.split("\n"):
        safe_line = line.encode("latin-1", errors="replace").decode("latin-1")
        if safe_line.strip():
            pdf.write(6, safe_line)
        pdf.ln(6)

    return pdf.output()


def generate_document(job_id: int, doc_type: str) -> dict:
    """Generate a resume or cover letter for a job.

    Returns: {"download_url": str, "cached": bool}
    """
    if doc_type not in ("resume", "cover_letter"):
        raise ValueError(f"Invalid doc_type: {doc_type}")

    # Load master resume and compute hash
    resume_content, resume_hash = _load_master_resume()

    # Build prompt hash for cache key
    prompt_hash = hashlib.sha256(f"{job_id}:{doc_type}:{resume_hash}".encode()).hexdigest()[:16]

    # Check cache
    cached = _check_cache(job_id, doc_type, prompt_hash)
    if cached:
        url = supabase_storage.get_signed_url(cached["storage_path"])
        return {"download_url": url, "cached": True}

    # Fetch job and description
    job = _get_job(job_id)
    description = _get_description(job)

    # Load system prompt
    system_prompt = _load_prompt(doc_type)

    # Build user prompt
    user_prompt = f"""## Master Resume
{resume_content}

## Job Details
- **Title:** {job['title']}
- **Company:** {job['company']}
- **Location:** {job['location']}

## Job Description
{description}
"""

    # Generate with LLM
    logger.info(f"Generating {doc_type} for job {job_id} ({job['company']} - {job['title']})")
    generated_text = generate_text(system_prompt, user_prompt)

    # Convert to PDF
    pdf_bytes = _text_to_pdf(generated_text)

    # Upload to Supabase Storage
    company_slug = job["company"].lower().replace(" ", "-")[:30]
    storage_path = f"{doc_type}s/{job_id}_{company_slug}_{prompt_hash}.pdf"
    supabase_storage.upload_file(storage_path, pdf_bytes)

    # Record in database
    from backend.config import settings
    supabase.table("generated_documents").insert({
        "job_id": job_id,
        "doc_type": doc_type,
        "storage_path": storage_path,
        "llm_model": settings.nvidia_model,
        "prompt_hash": prompt_hash,
    }).execute()

    # Get download URL
    url = supabase_storage.get_signed_url(storage_path)
    return {"download_url": url, "cached": False}
