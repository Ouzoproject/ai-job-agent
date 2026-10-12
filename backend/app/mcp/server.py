from dotenv import load_dotenv
from mcp.server import MCPServer

from app.models.job import Job, JobSummary, WebResult
from app.services.sources import web_search
from app.services.sources import registry
from app.services.sources.aggregator import search_all
from app.services.sources.base import SearchParams

load_dotenv()

mcp = MCPServer("Job Search MCP Server")

# Search for jobs
@mcp.tool()
async def search_jobs(
    query: str,
    location: str = "Germany",
    max_results: int = 50,
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
    Search for jobs in Germany across several job databases at once. Results are merged and
    de-duplicated. Returns lightweight job summaries; the id prefix shows
    the source (e.g. "ba:..."), and `snippet` holds a short description
    when the source provides one.
    Args:
        query: Search keywords.
        location: City, region, or country. Defaults to "Germany".
        max_results: Maximum number of results to return (default 50).
        radius_km: Search radius in kilometers around the location.
        employment_types: Filter by employment type(s), e.g. ["full-time"].
        published_within_days: Only return jobs published within this many days.
        contract_type: Filter by contract type, e.g. "permanent".
        offer_type: Filter by offer type, e.g. "internship".
        employer: Filter by employer name.
        profession_field: Filter by profession field, e.g. "IT & Development".
        include_temp_agency_jobs: Whether to include temp agency jobs (default True).
    """

    return await search_all(
        SearchParams(
            query=query,
            location=location,
            max_results=max_results,
            radius_km=radius_km,
            employment_types=employment_types,
            published_within_days=published_within_days,
            contract_type=contract_type,
            offer_type=offer_type,
            employer=employer,
            profession_field=profession_field,
            include_temp_agency_jobs=include_temp_agency_jobs,
        )
    )

# get job details of a specific job
@mcp.tool()
async def get_job_details(
    job_id: str,
) -> Job:
    """
    Get the full details of a specific job, including its complete
    description. Only works for job ids that start with "ba:". For other
    jobs, use read_webpage with the job's url.
    """

    return await registry.get_job(job_id)

#get job details of several jobs at once
@mcp.tool()
async def get_jobs_details(
    job_ids: list[str],
) -> list[Job]:
    """
    Get full details for several "ba:" jobs at once (fetched concurrently).
    Prefer this over repeated get_job_details calls. Ids from other
    sources are ignored; use read_webpage with their url instead.
    """

    return await registry.get_jobs(job_ids)


# Web tools are only offered to the agent when a search key is configured.
if web_search.is_configured():

    #get unstructured job postings from the open web
    @mcp.tool()
    async def search_web(
        query: str,
        max_results: int = 8,
    ) -> list[WebResult]:
        """
        Search the open web (company career pages, StepStone, Indeed,
        LinkedIn, Xing, ...). Use it when search_jobs returns few results,
        or to look up a specific company's jobs. Results are unverified
        snippets, not structured job data. Include German keywords such as
        "Stellenangebot" and the city for better hits.
        """

        return await web_search.search_web(query, max_results)
    
    #get the text content of a web page, e.g. a job posting found via search_jobs or search_web
    @mcp.tool()
    async def read_webpage(url: str) -> str:
        """
        Read the text content of a web page, e.g. a job posting found via
        search_jobs or search_web. Long pages are truncated.
        """

        return await web_search.read_webpage(url)


if __name__ == "__main__":
    mcp.run()