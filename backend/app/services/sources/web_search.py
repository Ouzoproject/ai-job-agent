import asyncio
import ipaddress
import os
import socket
from urllib.parse import urlsplit

import httpx

from app.models.job import WebResult

BASE_URL = "https://api.tavily.com"
TIMEOUT = 30.0
SNIPPET_CHARS = 400
PAGE_CHARS = 6000  # keep pages small enough for the agent's context


class WebSearchError(Exception):
    """Raised when the web search provider can't be reached or errors."""


async def _is_public_hostname(hostname: str) -> bool:
    try:
        addresses = await asyncio.to_thread(
            socket.getaddrinfo,
            hostname,
            None,
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror:
        return False

    resolved_ips = {address[4][0] for address in addresses}
    return bool(resolved_ips) and all(
        ipaddress.ip_address(address).is_global for address in resolved_ips
    )


async def validate_webpage_url(url: str) -> None:
    """Reject URLs that could target local or otherwise non-public services."""
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as exc:
        raise WebSearchError("Invalid webpage URL") from exc

    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or (port is not None and not 1 <= port <= 65535)
    ):
        raise WebSearchError("Only public HTTP(S) webpage URLs are allowed")

    try:
        hostname_ip = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        hostname_ip = None

    if hostname_ip is not None:
        is_public = hostname_ip.is_global
    else:
        is_public = await _is_public_hostname(parsed.hostname)

    if not is_public:
        raise WebSearchError("Only public HTTP(S) webpage URLs are allowed")


def is_configured() -> bool:
    return bool(os.getenv("TAVILY_API_KEY"))


async def _post(path: str, payload: dict) -> dict:
    headers = {"Authorization": f"Bearer {os.environ['TAVILY_API_KEY']}"}

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{BASE_URL}{path}",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise WebSearchError(
            f"Web search returned {exc.response.status_code}"
        ) from exc
    except httpx.RequestError as exc:
        raise WebSearchError(f"Could not reach web search: {exc}") from exc


async def search_web(query: str, max_results: int = 8) -> list[WebResult]:
    data = await _post(
        "/search",
        {
            "query": query,
            "max_results": min(max_results, 20),
            "search_depth": "basic",
            "country": "germany",  # boost German results
        },
    )

    return [
        WebResult(
            title=r.get("title", ""),
            url=r.get("url", ""),
            snippet=(r.get("content") or "")[:SNIPPET_CHARS],
        )
        for r in data.get("results", [])
    ]


async def read_webpage(url: str) -> str:
    await validate_webpage_url(url)
    data = await _post("/extract", {"urls": [url]})

    results = data.get("results") or []
    if not results:
        raise WebSearchError(f"Could not read the page at {url}")

    return (results[0].get("raw_content") or "")[:PAGE_CHARS]