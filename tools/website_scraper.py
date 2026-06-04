"""Website scraping tool for the company research crew."""

import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from crewai.tools import tool

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; CompanyResearchBot/1.0; +https://example.com/bot)"
    ),
}
_MAX_CHARS = 12_000


def _extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    cleaned = "\n".join(line for line in lines if line)
    return re.sub(r"\n{3,}", "\n\n", cleaned)


@tool("Scrape company website")
def scrape_company_website(url: str) -> str:
    """Scrape a company website URL and return the main text content."""
    raw = (url or "").strip()
    if not raw:
        return "Error: URL is empty."

    if not raw.startswith(("http://", "https://")):
        raw = f"https://{raw}"

    parsed = urlparse(raw)
    if not parsed.netloc:
        return f"Error: Invalid URL: {url}"

    try:
        response = requests.get(raw, headers=_HEADERS, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        return f"Error scraping {raw}: {exc}"

    content_type = response.headers.get("Content-Type", "")
    if "html" not in content_type.lower() and "<html" not in response.text[:500].lower():
        return f"Error: {raw} did not return HTML (Content-Type: {content_type})."

    text = _extract_text(response.text)
    if not text:
        return f"No readable text extracted from {raw}."

    if len(text) > _MAX_CHARS:
        text = text[:_MAX_CHARS] + "\n\n[Content truncated due to length.]"

    return f"URL: {raw}\n\n{text}"
