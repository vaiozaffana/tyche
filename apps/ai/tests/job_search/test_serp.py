import httpx
import pytest

from tyche_ai.job_search.models import ParsedQuery
from tyche_ai.job_search.tools.serp import (
    SERPAPI_URL,
    PermanentSearchProviderError,
    SerpApiProvider,
    TransientSearchProviderError,
)


def test_build_params_are_strict() -> None:
    provider = SerpApiProvider(api_key="secret", client=httpx.Client())
    query = ParsedQuery(
        target_roles=["tax accountant"],
        keywords=["brevet"],
        locations=["Surabaya"],
        date_posted="week",
    )

    assert provider.build_params(query, page_token="next") == {
        "engine": "google_jobs",
        "q": "tax accountant brevet",
        "location": "Surabaya",
        "hl": "id",
        "gl": "id",
        "chips": "date_posted:week",
        "next_page_token": "next",
        "api_key": "secret",
    }


def test_maps_jobs_and_prefers_configured_apply_url() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).startswith(SERPAPI_URL)
        return httpx.Response(
            200,
            json={
                "jobs_results": [
                    {
                        "job_id": "job-1",
                        "title": "Tax Accountant",
                        "company_name": "Acme",
                        "location": "Surabaya",
                        "via": "Google Jobs",
                        "description": "Requirements here",
                        "job_highlights": [
                            {"title": "Qualifications", "items": ["Brevet A", "Accurate"]}
                        ],
                        "apply_options": [
                            {"title": "Aggregator", "link": "https://example.com/job"},
                            {"title": "Glints", "link": "https://glints.com/id/job/1"},
                        ],
                        "detected_extensions": {"posted_at": "2 days ago", "salary": "Rp 8 jt"},
                    }
                ],
                "serpapi_pagination": {"next_page_token": "page-2"},
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = SerpApiProvider(api_key="secret", client=client).search(
        ParsedQuery(target_roles=["accountant"])
    )

    assert result.next_page_token == "page-2"
    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert candidate.source_url == "https://glints.com/id/job/1"
    assert candidate.source_site == "glints.com"
    assert candidate.highlights == ["Brevet A", "Accurate"]
    assert candidate.salary_raw == "Rp 8 jt"


@pytest.mark.parametrize(
    ("status", "error_type"),
    [
        (400, PermanentSearchProviderError),
        (429, TransientSearchProviderError),
        (503, TransientSearchProviderError),
    ],
)
def test_classifies_http_failures(status: int, error_type: type[Exception]) -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(status, text="error"))
    )

    with pytest.raises(error_type):
        SerpApiProvider(api_key="secret", client=client).search(
            ParsedQuery(target_roles=["accountant"])
        )
