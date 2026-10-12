from pydantic import BaseModel

class JobQuery(BaseModel):
    roles: list[str]

    locations: list[str] = ["Germany"]

    keywords: list[str] = []

    remote: bool | None = None

    employment_types: list[str] = []

    seniority: list[str] = []

class Job(BaseModel):
    id: str
    title: str
    company: str
    locations: list[str]
    employment_type: str
    description: str
    url: str
    source: str
    home_office: bool | None = None
    publication_date: str | None = None
    last_updated: str | None = None

class JobSummary(BaseModel):
    id: str
    title: str
    company: str
    locations: list[str]
    employment_type: str
    url: str
    source: str
    snippet: str | None = None


class WebResult(BaseModel):
    title: str
    url: str
    snippet: str