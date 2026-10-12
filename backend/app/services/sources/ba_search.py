import asyncio
import base64

import httpx

from app.models.job import Job, JobSummary


BA_BASE_URL = (
    "https://rest.arbeitsagentur.de/"
    "jobboerse/jobsuche-service"
)

BA_API_KEY = "jobboerse-jobsuche"

HEADERS = {
    "X-API-Key": BA_API_KEY,
}

DEFAULT_TIMEOUT = 30.0

MAX_PAGE_SIZE = 100

EMPLOYMENT_TYPE_CODES = {
    "full_time": "vz",
    "part_time": "tz",
    "shift_night_weekend": "snw",
    "home_office": "ho",
    "minijob": "mj",
}

CONTRACT_TYPE_CODES = {
    "fixed_term": "1",
    "permanent": "2",
}

OFFER_TYPE_CODES = {
    "job": "1",
    "self_employed": "2",
    "apprenticeship": "4",
    "internship": "34",
}
class JobSearchError(Exception):
    """Raised when the BA Jobsuche API can't be reached or returns an error."""

def encode_reference(reference: str) -> str:
    """
    Encode a BA reference number for the job-details endpoint.
    """
    return base64.b64encode(
        reference.encode("utf-8")
    ).decode("utf-8")


def _extract_locations(
    job_data: dict,
    fallback: str | None = None,
) -> list[str]:
    """
    Extract all job locations from BA data.    

    Handles two location-list shapes seen across BA endpoints:
    - `stellenlokationen`: [{"adresse": {"ort": ...}}, ...]  (search results,
      confirmed working against /pc/v6/jobs)
    - `arbeitsorte`: [{"ort": ...}, ...]  (documented shape for
      /pc/v4/jobdetails — unconfirmed against a live response, kept as a
      defensive fallback)
    """
 
    locations = (
        job_data.get("stellenlokationen")
        or job_data.get("arbeitsorte")
        or []
    )

    extracted_locations = []

    for location in locations:
        address = location.get(
            "adresse",
            location,  # fallback to the location dict itself if no "adresse" key
        )

        city = address.get("ort")

        if city:
            extracted_locations.append(city)

    # Remove duplicates while preserving order
    unique_locations = list(
        dict.fromkeys(extracted_locations)
    )

    if unique_locations:
        return unique_locations

    if fallback:
        return [fallback]

    return []


def _extract_employment_type(
    job_data: dict,
) -> str:
    """
    Extract and normalize employment type.    

    """
 
    models = job_data.get("arbeitszeitmodelle")
 
    if isinstance(models, list) and models:
        models_upper = {str(m).upper() for m in models}
 
        if "VOLLZEIT" in models_upper:
            return "Full-time"
 
        if models_upper & {
            "TEILZEIT",
            "MINIJOB",
            "SCHICHT_NACHTARBEIT_WOCHENENDE",
        }:
            return "Part-time"
 
        return "Other"
 
    if job_data.get("arbeitszeitVollzeit"):
        return "Full-time"
 
    elif (
        job_data.get("arbeitszeitTeilzeitVormittag")
        or job_data.get("arbeitszeitTeilzeitNachmittag")
        or job_data.get("arbeitszeitTeilzeitAbend")
        or job_data.get("arbeitszeitTeilzeitFlexibel")
    ):
        return "Part-time"
 
    return "Other"

def _extract_home_office(job_data: dict) -> bool | None:
    """
    Extract whether a job allows home office / remote work.
    """
 
    models = job_data.get("arbeitszeitmodelle")
 
    if isinstance(models, list):
        return any(
            "HEIM" in str(m).upper() or "TELEARBEIT" in str(m).upper()
            for m in models
        )
 
    return None

def _build_search_params(
    query: str,
    location: str,
    page: int,
    size: int,
    radius_km: int | None,
    employment_types: list[str] | None,
    published_within_days: int | None,
    contract_type: str | None,
    offer_type: str | None,
    employer: str | None,
    profession_field: str | None,
    include_temp_agency_jobs: bool,
) -> dict:
    """
    Build query parameters for the BA Jobsuche API search endpoint.
    """
 
    params: dict = {
        "was": query,
        "wo": location,
        "page": page,
        "size": size,
        "zeitarbeit": include_temp_agency_jobs,
    }
 
    if radius_km is not None:
        params["umkreis"] = radius_km
 
    if employment_types:
        codes = []
        for value in employment_types:
            code = EMPLOYMENT_TYPE_CODES.get(value)
            if code is None:
                raise ValueError(
                    f"Unknown employment_type '{value}'. "
                    f"Valid values: {sorted(EMPLOYMENT_TYPE_CODES)}"
                )
            codes.append(code)
        params["arbeitszeit"] = ";".join(codes)
 
    if published_within_days is not None:
        if not 0 <= published_within_days <= 100:
            raise ValueError(
                "published_within_days must be between 0 and 100"
            )
        params["veroeffentlichtseit"] = published_within_days
 
    if contract_type is not None:
        code = CONTRACT_TYPE_CODES.get(contract_type)
        if code is None:
            raise ValueError(
                f"Unknown contract_type '{contract_type}'. "
                f"Valid values: {sorted(CONTRACT_TYPE_CODES)}"
            )
        params["befristung"] = code
 
    if offer_type is not None:
        code = OFFER_TYPE_CODES.get(offer_type)
        if code is None:
            raise ValueError(
                f"Unknown offer_type '{offer_type}'. "
                f"Valid values: {sorted(OFFER_TYPE_CODES)}"
            )
        params["angebotsart"] = code
 
    if employer:
        params["arbeitgeber"] = employer
 
    if profession_field:
        params["berufsfeld"] = profession_field
 
    return params

async def search_jobs(
    query: str,
    location: str = "Germany",
    size: int = 50,
    max_results: int | None = None,
    radius_km: int | None = None,
    employment_types: list[str] | None = None,
    published_within_days: int | None = None,
    contract_type: str | None = None,
    offer_type: str | None = None,
    employer: str | None = None,
    profession_field: str | None = None,
    include_temp_agency_jobs: bool = True,
) -> list[JobSummary]:
    """
    Search for jobs using the BA Jobsuche API.
    """
 
    url = f"{BA_BASE_URL}/pc/v6/jobs"
    page_size = min(size, MAX_PAGE_SIZE)
    target = max_results if max_results is not None else page_size
 
    jobs: list[JobSummary] = []
    seen_ids: set[str] = set()
 
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
 
        page = 1
 
        while len(jobs) < target:
 
            params = _build_search_params(
                query=query,
                location=location,
                page=page,
                size=page_size,
                radius_km=radius_km,
                employment_types=employment_types,
                published_within_days=published_within_days,
                contract_type=contract_type,
                offer_type=offer_type,
                employer=employer,
                profession_field=profession_field,
                include_temp_agency_jobs=include_temp_agency_jobs,
            )
 
            try:
                response = await client.get(
                    url,
                    headers=HEADERS,
                    params=params,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise JobSearchError(
                    f"BA Jobsuche API returned "
                    f"{exc.response.status_code} for page {page}"
                ) from exc
            except httpx.RequestError as exc:
                raise JobSearchError(
                    f"Could not reach BA Jobsuche API: {exc}"
                ) from exc
 
            data = response.json()
            results = data.get("ergebnisliste", [])
 
            if not results:
                break
 
            for job_data in results:
 
                job_id = job_data["referenznummer"]
 
                # Skip duplicate postings
                if job_id in seen_ids:
                    continue
 
                seen_ids.add(job_id)
 
                jobs.append(
                    JobSummary(
                        id=job_id,
                        title=job_data.get(
                            "stellenangebotsTitel",
                            "Unknown title",
                        ),
                        company=job_data.get(
                            "firma",
                            "Unknown company",
                        ),
                        locations=_extract_locations(
                            job_data,
                            fallback=location,
                        ),
                        employment_type=_extract_employment_type(
                            job_data
                        ),
                        url=job_data.get(
                            "externeURL",
                            "",
                        ),
                        source="Bundesagentur für Arbeit",
                    )
                )
 
                if len(jobs) >= target:
                    break
 
            if len(results) < page_size:
                # Fewer results than requested means this was the last page.
                break
 
            page += 1
 
        return jobs[:target]
 
async def _get_job_details(
    job_id: str,
    client: httpx.AsyncClient,
) -> Job:
    """
    Get detailed information about a job
    using its BA reference number.
    """
 
    encoded_reference = encode_reference(job_id)
 
    url = (
        f"{BA_BASE_URL}/pc/v4/jobdetails/"
        f"{encoded_reference}"
    )
 
    try:
        response = await client.get(
            url,
            headers=HEADERS,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise JobSearchError(
            f"BA Jobsuche API returned "
            f"{exc.response.status_code} for job {job_id}"
        ) from exc
    except httpx.RequestError as exc:
        raise JobSearchError(
            f"Could not reach BA Jobsuche API: {exc}"
        ) from exc
 
    data = response.json()
 
    return Job(
        id=data.get("referenznummer", job_id),
        title=data.get(
            "stellenangebotsTitel",
            "Unknown title",
        ),
        
        company=(
            data.get("arbeitgeber")
            or data.get("firma")
            or "Unknown company"
        ),
        locations=_extract_locations(data),
        employment_type=_extract_employment_type(data),
        description=data.get(
            "stellenangebotsBeschreibung",
            "",
        ),
        url=data.get(
            "externeURL",
            "",
        ),
        source="Bundesagentur für Arbeit",
        home_office=_extract_home_office(data),
        publication_date=(
            data.get("aktuelleVeroeffentlichungsdatum")
            or data.get("ersteVeroeffentlichungsdatum")
        ),
        last_updated=data.get("modifikationsTimestamp"),
    )
 
 
async def get_job_details(
    job_id: str,
) -> Job:
    """
    Get detailed information about a job.
    """
 
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        return await _get_job_details(
            job_id,
            client,
        )

async def get_jobs_details(
    job_ids: list[str],
) -> list[Job]:
    """
    Get detailed information about multiple jobs in parallel.
    """
 
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        results = await asyncio.gather(
            *(_get_job_details(job_id, client) for job_id in job_ids),
            return_exceptions=True,
        )
 
    jobs: list[Job] = []
 
    for result in results:
        if isinstance(result, BaseException):
            continue
        jobs.append(result)
 
    return jobs