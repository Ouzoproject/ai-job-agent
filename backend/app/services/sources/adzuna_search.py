import html
import os
import re

import httpx

from app.models.job import JobSummary
from app.services.sources.base import SearchParams, SourceError

BASE_URL = "https://api.adzuna.com/v1/api/jobs/de/search"

PAGE_SIZE = 50          
MAX_PAGES = 10          
DEFAULT_RADIUS_KM = 25  
SNIPPET_CHARS = 300
TIMEOUT = 30.0

NATIONWIDE = {"", "germany", "deutschland"}

_TAGS = re.compile(r"<[^>]+>")
_EMPLOYMENT = {"full_time": "Full-time", "part_time": "Part-time"}


def is_configured() -> bool:
    return bool(os.getenv("ADZUNA_APP_ID") and os.getenv("ADZUNA_APP_KEY"))


def _clean(text: str | None) -> str:
    """Adzuna wraps matched keywords in <strong> tags; strip tags/entities."""
    return " ".join(html.unescape(_TAGS.sub("", text or "")).split())


def _build_params(p: SearchParams, page_size: int) -> dict:
    params: dict = {
        "app_id": os.environ["ADZUNA_APP_ID"],
        "app_key": os.environ["ADZUNA_APP_KEY"],
        "what": p.query,
        "results_per_page": page_size,
        "content-type": "application/json",
    }

    if p.location.strip().lower() not in NATIONWIDE:
        params["where"] = p.location
        params["distance"] = p.radius_km or DEFAULT_RADIUS_KM

    if p.published_within_days:
        params["max_days_old"] = p.published_within_days

    if p.employer:
        params["company"] = p.employer

    types = set(p.employment_types or [])
    if "full_time" in types and "part_time" not in types:
        params["full_time"] = 1
    elif "part_time" in types and "full_time" not in types:
        params["part_time"] = 1

    if p.contract_type == "permanent":
        params["permanent"] = 1

    return params


def _to_summary(item: dict, fallback_location: str) -> JobSummary:
    place = (item.get("location") or {}).get("display_name") or ""
    city = place.split(",")[0].strip() or fallback_location

    return JobSummary(
        id=f"adzuna:{item['id']}",
        title=_clean(item.get("title")) or "Unknown title",
        company=(item.get("company") or {}).get("display_name")
        or "Unknown company",
        locations=[city] if city else [],
        employment_type=_EMPLOYMENT.get(
            item.get("contract_time") or "", "Other"
        ),
        url=item.get("redirect_url", ""),
        source="Adzuna",
        snippet=_clean(item.get("description"))[:SNIPPET_CHARS] or None,
    )


async def search_jobs(p: SearchParams) -> list[JobSummary]:   
    if p.offer_type not in (None, "job"):
        return []

    page_size = min(p.max_results, PAGE_SIZE)
    jobs: list[JobSummary] = []
    seen: set[str] = set()

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for page in range(1, MAX_PAGES + 1):
            if len(jobs) >= p.max_results:
                break

            try:
                response = await client.get(
                    f"{BASE_URL}/{page}",
                    params=_build_params(p, page_size),
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise SourceError(
                    f"Adzuna returned {exc.response.status_code} "
                    f"for page {page}"
                ) from exc
            except httpx.RequestError as exc:
                raise SourceError(f"Could not reach Adzuna: {exc}") from exc

            results = response.json().get("results", [])

            for item in results:
                summary = _to_summary(item, p.location)
                if summary.id not in seen:
                    seen.add(summary.id)
                    jobs.append(summary)

            if len(results) < page_size:
                break  # last page

    return jobs[: p.max_results]