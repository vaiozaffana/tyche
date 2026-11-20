"""Firecrawl individual-posting reader."""

from typing import Any, Protocol, cast

from firecrawl.v1.client import V1FirecrawlApp

from tyche_ai.job_search.models import PageContent

MAX_PAGE_CHARS = 20_000
JOB_WORDS = ("job", "role", "lowongan", "pekerjaan", "kualifikasi", "requirements")
BLOCKED_MARKERS = ("sign in to view", "log in to view", "captcha", "verify you are human")


class PageReader(Protocol):
    def read(self, url: str) -> PageContent: ...


class _ScrapeResponse(Protocol):
    markdown: str | None


class _FirecrawlClient(Protocol):
    def scrape_url(self, url: str, **kwargs: Any) -> _ScrapeResponse: ...


class FirecrawlPageReader:
    def __init__(
        self,
        *,
        api_key: str,
        client: _FirecrawlClient | None = None,
        timeout_ms: int = 30_000,
    ) -> None:
        self.client = client or cast(_FirecrawlClient, V1FirecrawlApp(api_key=api_key))
        self.timeout_ms = timeout_ms

    def read(self, url: str) -> PageContent:
        try:
            response = self.client.scrape_url(
                url,
                formats=["markdown"],
                only_main_content=True,
                timeout=self.timeout_ms,
            )
            markdown = (response.markdown or "").strip()[:MAX_PAGE_CHARS]
        except Exception:
            return PageContent(status="failed", error="Firecrawl request failed")
        if self._blocked(markdown):
            return PageContent(status="blocked", markdown=markdown, error="Page content is blocked")
        return PageContent(status="ok", markdown=markdown)

    @staticmethod
    def _blocked(markdown: str) -> bool:
        lowered = markdown.lower()
        has_job_content = any(word in lowered for word in JOB_WORDS)
        return (
            len(markdown) < 120 or any(marker in lowered for marker in BLOCKED_MARKERS)
        ) and not has_job_content
