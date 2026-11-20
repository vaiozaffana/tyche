import pytest

from tyche_ai.job_search import cli_probe
from tyche_ai.job_search.cli_probe import PROBE_QUERIES, run_probe
from tyche_ai.job_search.models import Candidate, ParsedQuery, SearchPage
from tyche_ai.job_search.tools.serp import PermanentSearchProviderError


class FakeProvider:
    def search(self, query: ParsedQuery, *, page_token: str | None = None) -> SearchPage:
        del query, page_token
        return SearchPage(
            candidates=[
                Candidate(
                    title="Role",
                    company="Acme",
                    location="Remote",
                    source_site="glints.com",
                    description="short",
                ),
                Candidate(
                    title="Role",
                    company="Beta",
                    location="Jakarta",
                    source_site="linkedin.com",
                    description="x" * 500,
                ),
            ]
        )


def test_probe_aggregates_all_queries_without_pagination() -> None:
    summary = run_probe(FakeProvider())

    assert summary.counts == [2] * len(PROBE_QUERIES)
    assert summary.source_counts == {"glints": 15, "linkedin": 15}
    assert summary.short_descriptions == 15
    assert summary.total_candidates == 30


def test_live_probe_rejection_is_safe(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class RejectProvider:
        def __init__(self, *, api_key: str) -> None:
            assert api_key == "configured"

        def search(self, query: ParsedQuery, *, page_token: str | None = None) -> SearchPage:
            del query, page_token
            raise PermanentSearchProviderError("sensitive provider detail")

    monkeypatch.setenv("SERPAPI_API_KEY", "configured")
    monkeypatch.setattr(cli_probe, "SerpApiProvider", RejectProvider)

    assert cli_probe.main() == 1
    assert capsys.readouterr().out == (
        "FAILED: SerpApi rejected the probe; no live coverage claim was made.\n"
    )
