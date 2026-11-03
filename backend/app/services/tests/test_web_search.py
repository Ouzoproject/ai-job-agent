import pytest

from app.services.sources.web_search import WebSearchError, validate_webpage_url


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/admin",
        "http://localhost/admin",
        "http://169.254.169.254/latest/meta-data",
        "file:///etc/passwd",
        "http://user:password@example.com/",
    ],
)
async def test_validate_webpage_url_rejects_non_public_urls(url: str) -> None:
    with pytest.raises(WebSearchError):
        await validate_webpage_url(url)


@pytest.mark.asyncio
async def test_validate_webpage_url_accepts_public_hostname(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def public_hostname(_: str) -> bool:
        return True

    monkeypatch.setattr(
        "app.services.sources.web_search._is_public_hostname",
        public_hostname,
    )

    await validate_webpage_url("https://jobs.example.com/posting")
