"""NVIDIA Cloud LLM client (OpenAI-compatible API)."""

import logging

from openai import OpenAI

from backend.config import settings

logger = logging.getLogger(__name__)


def _get_client() -> OpenAI:
    return OpenAI(
        base_url=settings.nvidia_base_url,
        api_key=settings.nvidia_api_key,
    )


def generate_text(system_prompt: str, user_prompt: str) -> str:
    """Send a prompt to the NVIDIA Cloud LLM and return the response text."""
    client = _get_client()
    response = client.chat.completions.create(
        model=settings.nvidia_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=4096,
    )
    return response.choices[0].message.content or ""
