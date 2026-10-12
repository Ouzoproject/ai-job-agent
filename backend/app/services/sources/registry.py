from app.models.job import Job, JobSummary
from app.services.sources import adzuna_search, ba_search
from app.services.sources.base import SearchParams, Source

BA_JOB_URL = "https://www.arbeitsagentur.de/jobsuche/jobdetail/{ref}"

NO_DETAILS_MESSAGE = (
    "Full details are only available for job ids that start with 'ba:'. "
    "For other jobs, use read_webpage with the job's url."
)


# --- Bundesagentur für Arbeit --------------------

def _tag_ba(job: JobSummary | Job) -> None:
    """Prefix the id with the source and make sure the job has a link."""
    job.url = job.url or BA_JOB_URL.format(ref=job.id)
    job.id = f"ba:{job.id}"


async def _search_ba(p: SearchParams) -> list[JobSummary]:
    jobs = await ba_search.search_jobs(
        query=p.query,
        location=p.location,
        max_results=p.max_results,
        radius_km=p.radius_km,
        employment_types=p.employment_types,
        published_within_days=p.published_within_days,
        contract_type=p.contract_type,
        offer_type=p.offer_type,
        employer=p.employer,
        profession_field=p.profession_field,
        include_temp_agency_jobs=p.include_temp_agency_jobs,
    )
    for job in jobs:
        _tag_ba(job)
    return jobs


async def get_job(job_id: str) -> Job:
    if not job_id.startswith("ba:"):
        raise ValueError(NO_DETAILS_MESSAGE)

    job = await ba_search.get_job_details(job_id.removeprefix("ba:"))
    _tag_ba(job)
    return job


async def get_jobs(job_ids: list[str]) -> list[Job]:
    refs = [i.removeprefix("ba:") for i in job_ids if i.startswith("ba:")]
    if not refs:
        raise ValueError(NO_DETAILS_MESSAGE)

    jobs = await ba_search.get_jobs_details(refs)
    for job in jobs:
        _tag_ba(job)
    return jobs


# --- Registry ---------------------------------------------------------------

SOURCES: list[Source] = [
    Source("ba", _search_ba),
    Source(
        "adzuna",
        adzuna_search.search_jobs,
        enabled=adzuna_search.is_configured,
    ),
]