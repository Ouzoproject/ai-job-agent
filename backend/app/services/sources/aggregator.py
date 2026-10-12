import asyncio
import logging
import re
from itertools import zip_longest

from app.models.job import JobSummary
from app.services.sources.base import SearchParams, SourceError
from app.services.sources.registry import SOURCES

log = logging.getLogger(__name__)

# Words ignored when comparing titles/companies for duplicates.
_NOISE = {
    "m", "w", "d", "f", "x", "divers", "diverse",
    "gmbh", "mbh", "ag", "se", "kg", "ug", "ohg", "co", "ev",
}


def _norm(text: str) -> str:
    text = re.sub(r"\(.*?\)", " ", text.lower())  # drops "(m/w/d)" etc.
    return " ".join(w for w in re.findall(r"\w+", text) if w not in _NOISE)


def _dedupe_key(job: JobSummary) -> tuple:
    if job.company in ("", "Unknown company"):
        return ("id", job.id)  # can't compare reliably, keep it

    city = job.locations[0].split(",")[0] if job.locations else ""
    return (_norm(job.title), _norm(job.company), _norm(city))


def _merge(groups: list[list[JobSummary]], limit: int) -> list[JobSummary]:
    seen: set[tuple] = set()
    merged: list[JobSummary] = []

    for row in zip_longest(*groups):  # one job from each source per round
        for job in row:
            if job is None:
                continue

            key = _dedupe_key(job)
            if key in seen:
                continue
            seen.add(key)

            merged.append(job)
            if len(merged) >= limit:
                return merged

    return merged


async def search_all(params: SearchParams) -> list[JobSummary]:
    sources = [s for s in SOURCES if s.enabled()]

    results = await asyncio.gather(
        *(s.search(params) for s in sources),
        return_exceptions=True,
    )

    groups: list[list[JobSummary]] = []
    errors: list[str] = []

    for source, result in zip(sources, results):
        if isinstance(result, ValueError):           
            raise result
        if isinstance(result, BaseException):
            log.warning("Job source '%s' failed: %s", source.name, result)
            errors.append(f"{source.name}: {result}")
            continue
        groups.append(result)

    if not groups:
        raise SourceError("All job sources failed. " + "; ".join(errors))

    return _merge(groups, params.max_results)