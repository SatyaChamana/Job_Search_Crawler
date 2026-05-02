"""Supabase Storage helpers for uploading and downloading generated documents."""

import logging

from backend.database import supabase

logger = logging.getLogger(__name__)

BUCKET = "generated-docs"


def ensure_bucket():
    """Create the storage bucket if it doesn't exist."""
    try:
        supabase.storage.get_bucket(BUCKET)
    except Exception:
        supabase.storage.create_bucket(BUCKET, options={"public": False})
        logger.info(f"Created storage bucket: {BUCKET}")


def upload_file(path: str, content: bytes, content_type: str = "application/pdf") -> str:
    """Upload a file to Supabase Storage. Returns the storage path."""
    ensure_bucket()
    supabase.storage.from_(BUCKET).upload(
        path,
        content,
        file_options={"content-type": content_type, "upsert": "true"},
    )
    logger.info(f"Uploaded {path} to Supabase Storage")
    return path


def get_signed_url(path: str, expires_in: int = 3600) -> str:
    """Get a signed download URL for a stored file."""
    result = supabase.storage.from_(BUCKET).create_signed_url(path, expires_in)
    return result["signedURL"]
