"""Skill: web_search — search the web via DuckDuckGo.

Uses the DuckDuckGo Instant Answer API as primary source (free, no key).
Falls back to lightweight HTML scraping of DuckDuckGo search results
when the Instant Answer returns empty.

Contract: async def web_search(params: dict, context: dict) -> dict
"""

from __future__ import annotations

import logging
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from src.application.agent import skill_registry

logger = logging.getLogger(__name__)

_DDG_INSTANT_URL = "https://api.duckduckgo.com/"
_DDG_HTML_URL = "https://html.duckduckgo.com/html/"
_TIMEOUT = 10
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


async def _try_instant_answer(client: httpx.AsyncClient, query: str) -> list[dict]:
    """Try the DuckDuckGo Instant Answer API first."""
    try:
        resp = await client.get(
            _DDG_INSTANT_URL,
            params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
        )
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, ValueError):
        return []

    results: list[dict] = []

    # Abstract (main answer)
    if data.get("AbstractText"):
        results.append({
            "title": data.get("Heading", query),
            "url": data.get("AbstractURL", ""),
            "snippet": data["AbstractText"][:500],
        })

    # Related topics
    for topic in data.get("RelatedTopics", [])[:5]:
        if "Text" in topic:
            results.append({
                "title": topic.get("FirstURL", "").split("/")[-1].replace("_", " ") or query,
                "url": topic.get("FirstURL", ""),
                "snippet": topic["Text"][:300],
            })

    return results


async def _scrape_html_results(
    client: httpx.AsyncClient, query: str, max_results: int,
) -> list[dict]:
    """Fallback: scrape DuckDuckGo HTML search results page."""
    try:
        resp = await client.post(
            _DDG_HTML_URL,
            data={"q": query},
            headers={"User-Agent": _USER_AGENT},
        )
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("web_search HTML scrape failed: %s", exc)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results: list[dict] = []

    for item in soup.select(".result__body")[:max_results]:
        title_el = item.select_one(".result__title a")
        snippet_el = item.select_one(".result__snippet")

        title = title_el.get_text(strip=True) if title_el else ""
        url = title_el.get("href", "") if title_el else ""
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""

        if title or snippet:
            results.append({"title": title, "url": url, "snippet": snippet[:400]})

    return results


async def web_search(params: dict, context: dict) -> dict:
    """Search the web for information.

    Args:
        params: Must contain ``query`` (str). Optional ``max_results`` (int, default 3).
        context: Ignored by this skill.

    Returns:
        dict with key ``results``: list of {title, url, snippet}.
    """
    query = params.get("query", "").strip()
    max_results = int(params.get("max_results", 3))

    if not query:
        return {"results": [], "error": "Empty query"}

    async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
        # Try Instant Answer API first
        results = await _try_instant_answer(client, query)

        # If no meaningful results, fall back to HTML scraping
        if not results:
            results = await _scrape_html_results(client, query, max_results)

    return {"results": results[:max_results]}


# ── Auto-register ───────────────────────────────────────────────────
skill_registry.register(
    name="web_search",
    fn=web_search,
    description=(
        "Search the web for external information using DuckDuckGo. "
        "Use when you need data not available in the local database: "
        "product details, NCM codes, market prices, regulations, "
        "or any other publicly available information."
    ),
    params_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query in natural language",
            },
            "max_results": {
                "type": "integer",
                "description": "Max number of results to return (default: 3)",
                "default": 3,
            },
        },
        "required": ["query"],
    },
)
