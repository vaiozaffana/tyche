"""SerpApi Google Jobs discovery adapter."""

from typing import Any, Protocol, cast
from urllib.parse import urlparse

import httpx

from tyche_ai.job_search.models import Candidate, ParsedQuery, SearchPage

SERPAPI_URL = "https://serpapi.com/search.json"
DEFAULT_PREFERRED_HOSTS = ("jobstreet", "glints", "dealls", "kalibrr", "linkedin")


class SearchProviderError(RuntimeError):
    pass


class TransientSearchProviderError(SearchProviderError):
    pass


class PermanentSearchProviderError(SearchProviderError):
    pass


class JobSearchProvider(Protocol):
    def search(self, query: ParsedQuery, *, page_token: str | None = None) -> SearchPage: ...


class SerpApiProvider:
    def __init__(
        self,
        *,
        api_key: str,
        client: httpx.Client | None = None,
        preferred_hosts: tuple[str, ...] = DEFAULT_PREFERRED_HOSTS,
    ) -> None:
        self.api_key = api_key
        self.client = client or httpx.Client(timeout=20)
        self.preferred_hosts = preferred_hosts

    def build_params(self, query: ParsedQuery, *, page_token: str | None = None) -> dict[str, str]:
        params = {
            "engine": "google_jobs",
            "q": " ".join([*query.target_roles, *query.keywords]),
            "hl": "id",
            "gl": "id",
            "api_key": self.api_key,
        }
        if query.locations:
            params["location"] = ", ".join(query.locations)
        if query.date_posted:
            params["chips"] = f"date_posted:{query.date_posted}"
        if page_token:
            params["next_page_token"] = page_token
        return params

    def search(self, query: ParsedQuery, *, page_token: str | None = None) -> SearchPage:
        try:
            response = self.client.get(
                SERPAPI_URL, params=self.build_params(query, page_token=page_token)
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            if error.response.status_code in {408, 409, 429} or error.response.status_code >= 500:
                raise TransientSearchProviderError("SerpApi request failed") from error
            raise PermanentSearchProviderError("SerpApi request rejected") from error
        except httpx.TransportError as error:
            raise TransientSearchProviderError("SerpApi request failed") from error
        payload = cast(dict[str, Any], response.json())
        if payload.get("error"):
            raise PermanentSearchProviderError("SerpApi rejected the request")
        jobs = cast(list[dict[str, Any]], payload.get("jobs_results", []))
        pagination = cast(dict[str, Any], payload.get("serpapi_pagination", {}))
        return SearchPage(
            candidates=[self._candidate(job) for job in jobs],
            next_page_token=cast(str | None, pagination.get("next_page_token")),
        )

    def _candidate(self, job: dict[str, Any]) -> Candidate:
        source_url = self._source_url(cast(list[dict[str, Any]], job.get("apply_options", [])), job)
        detected = cast(dict[str, Any], job.get("detected_extensions", {}))
        highlights = [
            str(item)
            for group in cast(list[dict[str, Any]], job.get("job_highlights", []))
            for item in cast(list[Any], group.get("items", []))
        ]
        return Candidate(
            external_id=cast(str | None, job.get("job_id")),
            title=str(job.get("title", "")),
            company=str(job.get("company_name", "")),
            location=str(job.get("location", "")),
            source_url=source_url,
            source_site=urlparse(source_url).hostname
            if source_url
            else cast(str | None, job.get("via")),
            posted_at=cast(str | None, detected.get("posted_at")),
            description=str(job.get("description", "")),
            highlights=highlights,
            salary_raw=cast(str | None, detected.get("salary")),
        )

    def _source_url(self, options: list[dict[str, Any]], job: dict[str, Any]) -> str | None:
        links = [str(option["link"]) for option in options if option.get("link")]
        preferred = next(
            (
                link
                for link in links
                if any(host in (urlparse(link).hostname or "") for host in self.preferred_hosts)
            ),
            None,
        )
        return (
            preferred
            or next(iter(links), None)
            or cast(
                str | None,
                job.get("source_link") or job.get("share_link"),
            )
        )
