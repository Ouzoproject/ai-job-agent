from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from app.models.job import JobSummary


class SourceError(Exception):
    """Raised when a job source can't be reached or returns an error."""


@dataclass
class SearchParams:
    """
    Source-neutral search filters.

    Every source takes what it supports and ignores the rest.
    """

    query: str
    location: str = "Germany"
    max_results: int = 50
    radius_km: int | None = None
    employment_types: list[str] | None = None
    published_within_days: int | None = None
    contract_type: str | None = None
    offer_type: str | None = None
    employer: str | None = None
    profession_field: str | None = None
    include_temp_agency_jobs: bool = True


SearchFn = Callable[[SearchParams], Awaitable[list[JobSummary]]]


def _always_enabled() -> bool:
    return True


@dataclass(frozen=True)
class Source:
    """
    One job source.

    name:    short id, used as the prefix of job ids ("ba", "adzuna", ...)
    search:  async function taking SearchParams, returning JobSummary objects
    enabled: returns False when the source can't run (e.g. missing API key)
    """

    name: str
    search: SearchFn
    enabled: Callable[[], bool] = _always_enabled