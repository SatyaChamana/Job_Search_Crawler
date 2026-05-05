"""Orchestrator: get job description -> LLM generate -> docx/pdf bytes."""

import logging
from pathlib import Path

from backend.database import supabase
from backend.services.job_scraper import scrape_job_description
from backend.services.llm_client import generate_text
from backend.services.pdf_formatter import format_resume_docx, format_cover_letter_pdf

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
MASTER_RESUME_JSON = Path(__file__).parent.parent / "master_resume.json"
MASTER_RESUME_MD = Path(__file__).parent.parent.parent / "master_resume.md"


def _load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.txt"
    return path.read_text()


def _trim_master_resume(text: str) -> str:
    """Remove static sections (Projects, Education, Certifications, Awards, References, How To Use) from master resume to save tokens."""
    lines = text.split("\n")
    result = []
    skip = False
    skip_headers = {"## PROJECTS", "## EDUCATION", "## CERTIFICATIONS", "## AWARDS", "## REFERENCES", "## HOW TO USE"}

    for line in lines:
        stripped = line.strip().upper()
        if any(stripped.startswith(h) for h in skip_headers):
            skip = True
            continue
        if skip and line.startswith("## "):
            # New top-level section that's not in skip list — resume including
            skip = False
        if not skip:
            result.append(line)

    return "\n".join(result)


def _load_master_resume_md() -> str:
    """Load master resume markdown (data source with all bullet variants)."""
    if MASTER_RESUME_MD.exists():
        return MASTER_RESUME_MD.read_text()

    # Fallback to Supabase
    try:
        result = (
            supabase.table("master_resume")
            .select("content")
            .order("updated_at", desc=True)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]["content"]
    except Exception:
        pass

    raise RuntimeError(
        "No master resume found. Place master_resume.md in the project root "
        "or upload via PUT /api/master-resume."
    )


def _load_master_resume_json() -> str:
    """Load master resume JSON (output structure template)."""
    if MASTER_RESUME_JSON.exists():
        return MASTER_RESUME_JSON.read_text()
    raise RuntimeError("master_resume.json not found in backend/")


def _get_job(job_id: int) -> dict:
    """Fetch job from Supabase by database ID."""
    result = supabase.table("jobs").select("*").eq("id", job_id).single().execute()
    return result.data


def _get_description(job: dict) -> str:
    """Get job description: use cached if available, otherwise scrape and cache."""
    if job.get("description"):
        return job["description"]

    desc = scrape_job_description(job["url"])
    supabase.table("jobs").update({"description": desc}).eq("id", job["id"]).execute()
    return desc


def generate_document(job_id: int, doc_type: str) -> tuple[bytes, str]:
    """Generate a resume or cover letter for a job.

    Returns: (file_bytes, filename)
    """
    if doc_type not in ("resume", "cover_letter"):
        raise ValueError(f"Invalid doc_type: {doc_type}")

    master_resume_md = _load_master_resume_md()
    job = _get_job(job_id)
    description = _get_description(job)

    system_prompt = _load_prompt(doc_type)

    if doc_type == "resume":
        json_template = _load_master_resume_json()
        # Strip static sections from master resume to save tokens
        trimmed_resume = _trim_master_resume(master_resume_md)
        user_prompt = f"""## Master Resume (Data Source — cherry-pick from this)
{trimmed_resume}

## JSON Output Structure Template
{json_template}

## Job Details
- **Title:** {job['title']}
- **Company:** {job['company']}
- **Location:** {job['location']}

## Job Description
{description}
"""
    else:
        user_prompt = f"""## Master Resume
{master_resume_md}

## Job Details
- **Title:** {job['title']}
- **Company:** {job['company']}
- **Location:** {job['location']}

## Job Description
{description}
"""

    logger.info(f"Generating {doc_type} for job {job_id} ({job['company']} - {job['title']})")
    generated_text = generate_text(system_prompt, user_prompt)

    company_slug = job["company"].lower().replace(" ", "-").replace(" ", "")[:30]

    if doc_type == "resume":
        file_bytes = format_resume_docx(generated_text)
        filename = f"{company_slug}_resume.docx"
    else:
        file_bytes = format_cover_letter_pdf(generated_text)
        filename = f"{company_slug}_cover_letter.pdf"

    return file_bytes, filename
