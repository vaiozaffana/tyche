import logging
import time
from threading import Lock
from typing import TypeVar

import pytest
from pydantic import BaseModel

from tyche_ai.job_search.agents.dynamic.spec import PlannerOutput
from tyche_ai.job_search.graph.builder import build_job_search_graph, run_job_search
from tyche_ai.job_search.graph.context import RunContext
from tyche_ai.job_search.llm import ThinkingLevel
from tyche_ai.job_search.models import (
    Budget,
    Candidate,
    JobAssessment,
    PageContent,
    ParsedQuery,
    SearchPage,
)
from tyche_ai.job_search.settings import JobSearchSettings
from tyche_ai.job_search.tools.cache import InMemoryScrapeCache

from .test_dynamic_agents import planned

T = TypeVar("T", bound=BaseModel)


class GraphLLM:
    def __init__(self, *, empty_query: bool = False) -> None:
        self.empty_query = empty_query

    def invoke_structured(
        self,
        *,
        system: str,
        user: str,
        schema: type[T],
        thinking_level: ThinkingLevel,
        max_output_tokens: int,
    ) -> T:
        del system, thinking_level, max_output_tokens
        value: BaseModel
        if schema is ParsedQuery:
            value = (
                ParsedQuery()
                if self.empty_query
                else ParsedQuery(
                    target_roles=["backend developer"],
                    skills=["Python"],
                    language="en",
                )
            )
        elif schema is PlannerOutput:
            value = PlannerOutput(specialists=[planned()])
        else:
            scores = {
                "Backend Developer": 90,
                "Backend Engineer": 70,
                "Python Developer": 80,
            }
            score = next((score for title, score in scores.items() if title in user), 50)
            value = JobAssessment(
                fit_score=score,
                fit_reason="Match",
                tech_stack=["Python"],
                focus_findings={"tech_stack": ["Python"]},
                confidence="high",
            )
        return schema.model_validate(value)


class ConcurrentGraphLLM(GraphLLM):
    def __init__(self) -> None:
        super().__init__()
        self.active = 0
        self.max_active = 0
        self.lock = Lock()

    def invoke_structured(
        self,
        *,
        system: str,
        user: str,
        schema: type[T],
        thinking_level: ThinkingLevel,
        max_output_tokens: int,
    ) -> T:
        if schema is not JobAssessment:
            return super().invoke_structured(
                system=system,
                user=user,
                schema=schema,
                thinking_level=thinking_level,
                max_output_tokens=max_output_tokens,
            )
        with self.lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        try:
            time.sleep(0.05)
            return super().invoke_structured(
                system=system,
                user=user,
                schema=schema,
                thinking_level=thinking_level,
                max_output_tokens=max_output_tokens,
            )
        finally:
            with self.lock:
                self.active -= 1


class FixtureProvider:
    def __init__(self) -> None:
        self.calls = 0

    def search(self, query: ParsedQuery, *, page_token: str | None = None) -> SearchPage:
        del query, page_token
        self.calls += 1
        return SearchPage(
            candidates=[
                Candidate(
                    title="Backend Developer",
                    company="Acme",
                    location="Jakarta",
                    source_url="https://glints.com/job/1",
                    description="Short role",
                    posted_at="2 days ago",
                ),
                Candidate(
                    title="Backend Developer",
                    company="PT Acme Tbk",
                    location="Jakarta",
                    source_url="https://glints.com/job/1-duplicate",
                    description="Short duplicate",
                ),
                Candidate(
                    title="Backend Engineer",
                    company="Beta",
                    location="Remote",
                    source_url="https://linkedin.com/jobs/2",
                    description="Short role",
                ),
                Candidate(
                    title="Python Developer",
                    company="Gamma",
                    location="Bandung",
                    source_url="https://gamma.example/jobs/3",
                    description="Requirements " + "x" * 600,
                    salary_raw="Rp 15 jt",
                    posted_at="1 day ago",
                ),
                Candidate(
                    title="Sales Manager",
                    company="Delta",
                    location="Jakarta",
                    source_url="https://delta.example/jobs/4",
                    description="Requirements " + "x" * 600,
                ),
            ]
        )


class FixtureReader:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def read(self, url: str) -> PageContent:
        self.calls.append(url)
        return PageContent(status="ok", markdown="Requirements: Python and PostgreSQL")


def context(
    provider: FixtureProvider,
    reader: FixtureReader,
    cache: InMemoryScrapeCache,
    *,
    llm: GraphLLM | None = None,
    max_llm_jobs: int = 10,
    max_concurrency: int = 4,
) -> RunContext:
    settings = JobSearchSettings(
        job_search_max_serp_calls=1,
        job_search_max_firecrawl_calls=2,
        job_search_max_llm_jobs=max_llm_jobs,
        job_search_max_results=10,
        job_search_max_concurrency=max_concurrency,
    )
    return RunContext(
        search_id="test-search",
        llm=llm or GraphLLM(),
        provider=provider,
        reader=reader,
        cache=cache,
        settings=settings,
        budget=Budget(
            max_serp_calls=settings.job_search_max_serp_calls,
            max_firecrawl_calls=settings.job_search_max_firecrawl_calls,
            max_llm_jobs=settings.job_search_max_llm_jobs,
        ),
    )


def test_full_graph_gates_deduplicates_assesses_and_ranks() -> None:
    provider = FixtureProvider()
    reader = FixtureReader()

    result = run_job_search("backend Python jobs", context(provider, reader, InMemoryScrapeCache()))

    assert result.status == "completed"
    assert [job.candidate.title for job in result.results] == [
        "Backend Developer",
        "Python Developer",
        "Backend Engineer",
    ]
    assert reader.calls == ["https://glints.com/job/1-duplicate"]
    assert result.stats.candidates == 5
    assert result.stats.after_dedup == 4
    assert result.stats.after_filter == 3
    assert result.stats.firecrawl_calls == 1
    assert result.stats.llm_calls == 3
    gate_reasons = [entry["reason"] for entry in result.run_log if entry["event"] == "gate"]
    assert gate_reasons == ["needs_scrape", "domain_blocked", "description_sufficient"]


def test_gate_logs_only_safe_identifiers(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO):
        run_job_search(
            "private backend Python prompt",
            context(FixtureProvider(), FixtureReader(), InMemoryScrapeCache()),
        )

    messages = [
        record.getMessage() for record in caplog.records if "job_search_gate" in record.getMessage()
    ]
    assert messages
    assert all("test-search" in message and "reason=" in message for message in messages)
    assert all("private" not in message and "Short role" not in message for message in messages)


def test_cache_hit_avoids_second_page_read_and_charge() -> None:
    provider = FixtureProvider()
    reader = FixtureReader()
    cache = InMemoryScrapeCache()

    first = run_job_search("backend Python jobs", context(provider, reader, cache))
    second = run_job_search("backend Python jobs", context(provider, reader, cache))

    assert first.stats.firecrawl_calls == 1
    assert second.stats.firecrawl_calls == 0
    assert second.stats.cache_hits == 1
    assert len(reader.calls) == 1
    assert second.results[0].enrichment_status == "cached"


def test_assessment_budget_caps_fan_out() -> None:
    result = run_job_search(
        "backend Python jobs",
        context(FixtureProvider(), FixtureReader(), InMemoryScrapeCache(), max_llm_jobs=2),
    )

    assert len(result.results) == 2
    assert result.stats.llm_calls == 2


def test_assessment_fan_out_respects_concurrency() -> None:
    llm = ConcurrentGraphLLM()

    result = run_job_search(
        "backend Python jobs",
        context(
            FixtureProvider(),
            FixtureReader(),
            InMemoryScrapeCache(),
            llm=llm,
            max_concurrency=2,
        ),
    )

    assert len(result.results) == 3
    assert llm.max_active == 2


def test_parse_failure_stops_before_provider() -> None:
    provider = FixtureProvider()
    result = run_job_search(
        "asdf",
        context(provider, FixtureReader(), InMemoryScrapeCache(), llm=GraphLLM(empty_query=True)),
    )

    assert result.status == "failed"
    assert result.error_code == "prompt_parse"
    assert result.stats.serp_calls == 0
    assert provider.calls == 0


def test_parent_graph_topology_is_stable() -> None:
    assert set(build_job_search_graph().get_graph().nodes) == {
        "__start__",
        "analyze_query",
        "plan_specialists",
        "search_jobs",
        "dedupe_filter",
        "gate_and_read",
        "dispatch_assessments",
        "assess_job",
        "rank_and_finalize",
        "finalize",
        "__end__",
    }
