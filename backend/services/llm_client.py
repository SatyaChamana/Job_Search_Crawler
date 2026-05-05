"""LLM client supporting NVIDIA Cloud, Ollama (both OpenAI-compatible), and Anthropic."""

import logging

from openai import OpenAI

from backend.config import settings

logger = logging.getLogger(__name__)


def _get_openai_client() -> tuple[OpenAI, str]:
    """Return (client, model) for OpenAI-compatible providers."""
    provider = settings.llm_provider

    if provider == "nvidia":
        client = OpenAI(
            base_url=settings.nvidia_base_url,
            api_key=settings.nvidia_api_key,
        )
        model = settings.nvidia_model
        logger.info(f"Using NVIDIA Cloud: {model}")
    else:
        client = OpenAI(
            base_url=settings.ollama_base_url,
            api_key="ollama",
        )
        model = settings.ollama_model
        logger.info(f"Using Ollama: {model}")

    return client, model


def generate_text(system_prompt: str, user_prompt: str) -> str:
    """Send a prompt to the active LLM provider and return the response text."""
    if settings.llm_provider == "anthropic":
        return _generate_anthropic(system_prompt, user_prompt)
    if settings.llm_provider == "ollama":
        return _generate_ollama(system_prompt, user_prompt)

    # NVIDIA (OpenAI-compatible)
    client, model = _get_openai_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=8192,
    )
    return response.choices[0].message.content or ""


def _generate_ollama(system_prompt: str, user_prompt: str) -> str:
    """Generate text using Ollama's native API with proper context window."""
    import requests

    base_url = settings.ollama_base_url.replace("/v1", "")
    model = settings.ollama_model
    logger.info(f"Using Ollama: {model}")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
        {"role": "assistant", "content": "{"},
    ]

    response = requests.post(
        f"{base_url}/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_ctx": 32768,
                "temperature": 0.3,
                "num_predict": 8192,
            },
        },
        timeout=300,
    )
    response.raise_for_status()

    text = response.json().get("message", {}).get("content", "")
    if not text.strip().startswith("{"):
        text = "{" + text
    return text


def _generate_anthropic(system_prompt: str, user_prompt: str) -> str:
    """Generate text using the Anthropic API."""
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    logger.info(f"Using Anthropic: {settings.anthropic_model}")

    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=8192,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
        temperature=0.3,
    )
    return response.content[0].text
