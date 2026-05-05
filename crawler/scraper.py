"""Scrape and clean job descriptions from career page URLs."""

import logging
import re

from bs4 import BeautifulSoup

from crawler.fetcher import fetch_page
from crawler.browser import fetch_rendered_html

logger = logging.getLogger(__name__)

# Common selectors where job descriptions live
DESCRIPTION_SELECTORS = [
    '[data-automation-id="jobPostingDescription"]',  # Workday
    ".job-description",
    ".job-details",
    ".job-detail-description",
    "#job-description",
    "#job-details",
    '[class*="description"]',
    '[class*="job-detail"]',
    "article",
    "main",
]


def _extract_description(html: str) -> str:
    """Extract the job description text from HTML."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove script, style, nav, header, footer
    for tag in soup(["script", "style", "nav", "header", "footer", "noscript"]):
        tag.decompose()

    # Try known selectors first
    for selector in DESCRIPTION_SELECTORS:
        el = soup.select_one(selector)
        if el and len(el.get_text(strip=True)) > 200:
            return _clean_text(el.get_text(separator="\n", strip=True))

    # Fallback: largest text block in body
    body = soup.find("body")
    if body:
        return _clean_text(body.get_text(separator="\n", strip=True))

    return _clean_text(soup.get_text(separator="\n", strip=True))


def _clean_text(text: str) -> str:
    """Clean extracted text: collapse whitespace, limit length."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    if len(text) > 8000:
        text = text[:8000] + "\n\n[Description truncated]"
    return text.strip()


# Sites known to be JS-rendered — skip static fetch, go straight to Playwright
JS_RENDERED_DOMAINS = [
    "apply.careers.microsoft.com",   # Eightfold
    "jobs.lever.co",
    "careers.smartrecruiters.com",
]


def _is_quality_description(desc: str) -> bool:
    """Check if scraped text looks like a real job description, not meta tag dump."""
    if len(desc) < 300:
        return False
    # Real JDs have line breaks (sections, bullet points). Meta dumps are one big blob.
    line_count = desc.count("\n")
    if line_count < 5:
        return False
    return True


def scrape_job_description(url: str) -> str:
    """Scrape a job posting URL and return the cleaned description text.

    Tries a fast static fetch first, falls back to Playwright for JS-rendered pages.
    """
    # Skip static fetch for known JS-rendered sites
    skip_static = any(domain in url for domain in JS_RENDERED_DOMAINS)

    if not skip_static:
        try:
            response = fetch_page(url, timeout=15)
            desc = _extract_description(response.text)
            if _is_quality_description(desc):
                logger.info(f"Scraped description via static fetch ({len(desc)} chars)")
                return desc
            else:
                logger.debug(f"Static fetch returned low-quality content, trying browser")
        except Exception as e:
            logger.debug(f"Static fetch failed for {url}: {e}")

    # Fallback: browser rendering
    try:
        html = fetch_rendered_html(url, wait_ms=8000, timeout=25000)
        desc = _extract_description(html)
        logger.info(f"Scraped description via browser ({len(desc)} chars)")
        return desc
    except Exception as e:
        logger.error(f"Browser fetch also failed for {url}: {e}")
        raise RuntimeError(f"Could not scrape job description from {url}") from e
