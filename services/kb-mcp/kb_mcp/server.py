import os
from datetime import datetime, timezone
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

try:
    from mcp.server.transport_security import TransportSecuritySettings

    _security = TransportSecuritySettings(enable_dns_rebinding_protection=False)
except ImportError:
    _security = None

KB_API_BASE = os.environ.get("KB_API_BASE", "https://swanny.laughtale.co.uk").rstrip("/")
KB_SERVICE_TOKEN = os.environ.get("KB_SERVICE_TOKEN", "").strip()

mcp = FastMCP("knowledgebase", transport_security=_security) if _security else FastMCP("knowledgebase")


def _headers() -> dict[str, str]:
    if not KB_SERVICE_TOKEN:
        return {}
    return {
        "Authorization": f"Bearer {KB_SERVICE_TOKEN}",
        "X-KB-Service-Token": KB_SERVICE_TOKEN,
    }


_client = httpx.AsyncClient(base_url=KB_API_BASE, headers=_headers(), timeout=30.0)


@mcp.tool()
async def kb_search(
    query: str,
    limit: int = 10,
    tags: list[str] | None = None,
    type: str | None = None,
) -> list[dict[str, Any]]:
    """Semantic search over the personal knowledge base.

    Returns ranked nodes by vector similarity. Each result has id, title,
    abstract, tags, object_type, score, source_type, created_at, and time
    metadata exposed by the KnowledgeBase-S API.

    Args:
        query: natural-language question or keyword query.
        limit: max results, 1-50. Default 10.
        tags: optional list of tag strings to filter by.
        type: optional 'article' | 'entity' | 'summary' to filter by object type.
    """
    params: dict[str, Any] = {"q": query, "limit": max(1, min(limit, 50))}
    if tags:
        params["tags"] = ",".join(tags)
    if type:
        params["type"] = type
    r = await _client.get("/api/kb/search", params=params)
    r.raise_for_status()
    return r.json()


@mcp.tool()
async def kb_get_node(node_id: str) -> dict[str, Any]:
    """Fetch a single knowledge-base node by id, including its neighbors.

    The response includes the node body/abstract and an `edges` array listing
    every relation (from_node_id, to_node_id, edge_type).
    """
    r = await _client.get(f"/api/kb/node/{node_id}")
    r.raise_for_status()
    return r.json()


@mcp.tool()
async def get_current_time() -> dict[str, str]:
    """Return the current date and time in UTC.

    Use this whenever the user asks about today's date, the current time, or
    anything time-sensitive.
    """
    now = datetime.now(timezone.utc)
    return {
        "iso": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time_utc": now.strftime("%H:%M:%S UTC"),
        "weekday": now.strftime("%A"),
    }


@mcp.tool()
async def kb_get_ancestors(object_id: str) -> dict[str, Any]:
    """Return the index/folder ancestor chain for a node."""
    r = await _client.get(f"/api/kb/objects/{object_id}/ancestors")
    r.raise_for_status()
    return r.json()
