from typing import Any

from tyche_ai.job_search.tools.firecrawl import MAX_PAGE_CHARS, FirecrawlPageReader


class FakeFirecrawl:
    def __init__(self, markdown: str = "", error: Exception | None = None) -> None:
        self.markdown = markdown
        self.error = error
        self.kwargs: dict[str, Any] = {}

    def scrape_url(self, url: str, **kwargs: Any) -> Any:
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return type("Response", (), {"markdown": self.markdown})()


def reader(client: FakeFirecrawl) -> FirecrawlPageReader:
    return FirecrawlPageReader(api_key="not-real", client=client, timeout_ms=123)


def test_reads_main_markdown_and_truncates() -> None:
    client = FakeFirecrawl("Requirements " + "x" * MAX_PAGE_CHARS)

    result = reader(client).read("https://example.com/job")

    assert result.status == "ok"
    assert len(result.markdown) == MAX_PAGE_CHARS
    assert client.kwargs == {
        "formats": ["markdown"],
        "only_main_content": True,
        "timeout": 123,
    }


def test_returns_blocked_for_login_wall_without_job_content() -> None:
    result = reader(FakeFirecrawl("Sign in to view this page")).read("https://example.com/job")

    assert result.status == "blocked"


def test_returns_failed_instead_of_raising() -> None:
    result = reader(FakeFirecrawl(error=TimeoutError())).read("https://example.com/job")

    assert result.status == "failed"
    assert result.error == "Firecrawl request failed"
