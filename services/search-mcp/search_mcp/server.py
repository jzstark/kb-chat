import os
import re
from typing import Any

import httpx
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP

try:
    from mcp.server.transport_security import TransportSecuritySettings

    _security = TransportSecuritySettings(enable_dns_rebinding_protection=False)
except ImportError:
    _security = None

BRAVE_API_BASE = "https://api.search.brave.com"
BRAVE_SEARCH_API_KEY = os.environ.get("BRAVE_SEARCH_API_KEY", "").strip()

mcp = FastMCP("web-search", transport_security=_security) if _security else FastMCP("web-search")


def _headers() -> dict[str, str]:
    if not BRAVE_SEARCH_API_KEY:
        raise RuntimeError("BRAVE_SEARCH_API_KEY is not configured")
    return {
        "Accept": "application/json",
        "X-Subscription-Token": BRAVE_SEARCH_API_KEY,
    }


def _bounded(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))


def _add_optional(params: dict[str, Any], **values: Any) -> dict[str, Any]:
    for key, value in values.items():
        if value is not None and value != "":
            params[key] = value
    return params


async def _brave_get(path: str, params: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient(base_url=BRAVE_API_BASE, headers=_headers(), timeout=45.0) as client:
        response = await client.get(path, params=params)
        if response.status_code == 429:
            raise RuntimeError("Brave Search API rate limit exceeded")
        response.raise_for_status()
        return response.json()


def _simplify_web_results(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = payload.get("web", {}).get("results", [])
    simplified: list[dict[str, Any]] = []
    for item in results:
        simplified.append(
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "description": item.get("description"),
                "age": item.get("age"),
                "page_age": item.get("page_age"),
                "published": item.get("published"),
                "profile": item.get("profile"),
                "extra_snippets": item.get("extra_snippets"),
            }
        )
    return simplified


def _simplify_news_results(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = payload.get("results", [])
    simplified: list[dict[str, Any]] = []
    for item in results:
        simplified.append(
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "description": item.get("description"),
                "age": item.get("age"),
                "page_age": item.get("page_age"),
                "published": item.get("published"),
                "source": item.get("source"),
                "thumbnail": item.get("thumbnail"),
            }
        )
    return simplified


@mcp.tool()
async def brave_llm_context_search(
    query: str,
    freshness: str | None = None,
    country: str | None = None,
    search_lang: str = "en",
    count: int = 10,
    maximum_number_of_urls: int = 10,
    maximum_number_of_tokens: int = 8192,
    maximum_number_of_tokens_per_url: int = 2048,
    context_threshold_mode: str = "balanced",
) -> dict[str, Any]:
    """Search the web with Brave LLM Context for answer grounding.

    Use this as the default web-search tool when the user wants current
    information, source-grounded answers, or page content rather than only a
    list of links.

    Args:
        query: Search query, max 400 chars and 50 words.
        freshness: Optional Brave freshness filter such as 'pd' for the past
            day, 'pw' for past week, 'pm' for past month, 'py' for past year,
            or a Brave-supported custom date range.
        country: Optional 2-letter country code, for example 'US'.
        search_lang: Search language, default 'en'.
        count: Search results Brave should consider, 1-50.
        maximum_number_of_urls: Max URLs included in context, 1-50.
        maximum_number_of_tokens: Approximate total context token budget,
            1024-32768.
        maximum_number_of_tokens_per_url: Token budget per URL, 512-8192.
        context_threshold_mode: 'strict', 'balanced', 'lenient', or 'disabled'.
    """
    params = _add_optional(
        {
            "q": query,
            "search_lang": search_lang,
            "count": _bounded(count, 1, 50),
            "maximum_number_of_urls": _bounded(maximum_number_of_urls, 1, 50),
            "maximum_number_of_tokens": _bounded(maximum_number_of_tokens, 1024, 32768),
            "maximum_number_of_tokens_per_url": _bounded(maximum_number_of_tokens_per_url, 512, 8192),
            "context_threshold_mode": context_threshold_mode,
        },
        freshness=freshness,
        country=country,
    )
    payload = await _brave_get("/res/v1/llm/context", params)
    return {
        "query": query,
        "freshness_note": "Brave freshness is based on Brave's page/news freshness signals; for News Search, freshness is discovery date, not guaranteed publication date.",
        "grounding": payload.get("grounding"),
        "sources": payload.get("sources"),
    }


@mcp.tool()
async def brave_web_search(
    query: str,
    freshness: str | None = None,
    country: str | None = None,
    search_lang: str = "en",
    count: int = 10,
    site: str | None = None,
) -> list[dict[str, Any]]:
    """Search Brave Web Search and return ranked links with snippets.

    Use this when the user mainly asks to find pages or list links. For answer
    grounding, prefer brave_llm_context_search.
    """
    effective_query = f"site:{site} {query}" if site else query
    params = _add_optional(
        {
            "q": effective_query,
            "search_lang": search_lang,
            "count": _bounded(count, 1, 20),
            "extra_snippets": "true",
        },
        freshness=freshness,
        country=country,
    )
    return _simplify_web_results(await _brave_get("/res/v1/web/search", params))


@mcp.tool()
async def brave_news_search(
    query: str,
    freshness: str | None = "pd",
    country: str | None = None,
    search_lang: str = "en",
    count: int = 10,
) -> dict[str, Any]:
    """Search Brave News Search and return recent news links with snippets.

    Use this when the user explicitly asks for news or latest reports. Brave
    News Search freshness is based on discovery date, not guaranteed article
    publication date.
    """
    params = _add_optional(
        {
            "q": query,
            "search_lang": search_lang,
            "count": _bounded(count, 1, 50),
        },
        freshness=freshness,
        country=country,
    )
    return {
        "freshness_note": "Brave News Search freshness is discovery date, not guaranteed publication date.",
        "results": _simplify_news_results(await _brave_get("/res/v1/news/search", params)),
    }


@mcp.tool()
async def fetch_url(url: str, max_chars: int = 12000) -> dict[str, Any]:
    """Fetch a URL and extract readable text.

    Use this when the user gives a URL directly or when search snippets are not
    enough. The caller is responsible for respecting the source site's terms.
    """
    async with httpx.AsyncClient(
        headers={"User-Agent": "kb-chat search-mcp/1.0"},
        follow_redirects=True,
        timeout=30.0,
    ) as client:
        response = await client.get(url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return {
        "url": str(response.url),
        "status_code": response.status_code,
        "title": title,
        "text": text[: _bounded(max_chars, 1000, 50000)],
        "truncated": len(text) > max_chars,
    }
