import pytest

from tyche_ai.job_search.models import Budget, Candidate, ParsedQuery
from tyche_ai.job_search.screening.dedup import deduplicate
from tyche_ai.job_search.screening.gate import GateDecision, GateSettings, decide
from tyche_ai.job_search.screening.title_filter import title_matches


def candidate(**overrides: object) -> Candidate:
    values: dict[str, object] = {
        "title": "Tax Accountant",
        "company": "PT Acme Tbk",
        "location": "Surabaya",
        "source_url": "https://jobs.example.com/1",
        "description": "short",
    }
    values.update(overrides)
    return Candidate.model_validate(values)


def test_dedup_normalizes_legal_suffixes_and_keeps_preferred_url() -> None:
    first = candidate(description="a longer ordinary description")
    preferred = candidate(
        company="Acme",
        source_url="https://glints.com/id/job/1",
        description="short",
        highlights=["Brevet"],
    )

    result = deduplicate([first, preferred], preferred_hosts=("glints.com",))

    assert len(result) == 1
    assert result[0].source_url == preferred.source_url
    assert result[0].highlights == ["Brevet"]


@pytest.mark.parametrize(
    ("title", "role", "expected", "score"),
    [
        ("Senior Software Developer", "software pengembang", True, 1.0),
        ("Akuntan Pajak", "tax accountant", True, 0.5),
        ("Marketing Manager", "software engineer", False, 0.0),
    ],
)
def test_title_match_table(title: str, role: str, expected: bool, score: float) -> None:
    assert title_matches(candidate(title=title), ParsedQuery(target_roles=[role])) == (
        expected,
        score,
    )


def test_gate_reason_no_url() -> None:
    assert gate(candidate(source_url=None)).reason == "no_url"


def test_gate_reason_title_mismatch() -> None:
    assert gate(candidate(title="Sales Manager")).reason == "title_mismatch"


def test_gate_reason_description_sufficient() -> None:
    complete = candidate(description="Requirements " + "x" * 500)
    assert gate(complete).reason == "description_sufficient"


def test_gate_long_description_without_markers_still_needs_scrape() -> None:
    incomplete = candidate(description="x" * 600)
    assert gate(incomplete).reason == "needs_scrape"


def test_gate_reason_domain_blocked() -> None:
    assert gate(candidate(source_url="https://id.linkedin.com/jobs/1")).reason == "domain_blocked"


def test_gate_reason_budget_exhausted() -> None:
    budget = Budget(max_serp_calls=1, max_firecrawl_calls=0, max_llm_jobs=1)
    assert gate(candidate(), budget=budget).reason == "budget_exhausted"


def test_gate_reason_needs_scrape() -> None:
    decision = gate(candidate())
    assert decision.scrape
    assert decision.reason == "needs_scrape"


def gate(job: Candidate, *, budget: Budget | None = None) -> GateDecision:
    return decide(
        job,
        ParsedQuery(target_roles=["tax accountant"]),
        GateSettings(),
        budget or Budget(max_serp_calls=1, max_firecrawl_calls=1, max_llm_jobs=1),
    )
