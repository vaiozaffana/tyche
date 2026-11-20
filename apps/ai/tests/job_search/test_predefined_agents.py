from typing import Any

import pytest

from tyche_ai.job_search.agents.dynamic.spec import PlannerOutput
from tyche_ai.job_search.agents.predefined.job_scout import build_job_scout
from tyche_ai.job_search.agents.predefined.page_reader import build_page_reader
from tyche_ai.job_search.agents.predefined.query_analyst import (
    PromptParseError,
    build_query_analyst,
)
from tyche_ai.job_search.agents.predefined.registry import PREDEFINED_SUBAGENTS
from tyche_ai.job_search.agents.predefined.specialist_planner import build_specialist_planner
from tyche_ai.job_search.llm import FakeStructuredLLM
from tyche_ai.job_search.models import Budget, Candidate, PageContent, ParsedQuery, SearchPage
from tyche_ai.job_search.tools.cache import InMemoryScrapeCache

from .test_dynamic_agents import planned


class FakeProvider:
    def __init__(self) -> None:
        self.calls = 0

    def search(self, query: ParsedQuery, *, page_token: str | None = None) -> SearchPage:
        del query, page_token
        self.calls += 1
        return SearchPage(
            candidates=[Candidate(title="Engineer", company="Acme", location="Remote")]
        )


class FakeReader:
    def __init__(self) -> None:
        self.calls = 0

    def read(self, url: str) -> PageContent:
        del url
        self.calls += 1
        return PageContent(status="ok", markdown="Requirements " + "x" * 200)


def budget(**overrides: int) -> Budget:
    values = {"max_serp_calls": 1, "max_firecrawl_calls": 1, "max_llm_jobs": 1}
    values.update(overrides)
    return Budget(**values)


def test_query_analyst_maps_relative_date_and_retries() -> None:
    llm = FakeStructuredLLM()
    llm.add(
        ParsedQuery,
        ValueError("invalid"),
        ParsedQuery(target_roles=["accountant"], language="id"),
    )

    result = build_query_analyst(llm).invoke({"prompt": "Akuntan Surabaya seminggu terakhir"})

    assert result["parsed_query"].date_posted == "week"
    assert len(llm.calls) == 2


def test_query_analyst_rejects_empty_prompt_without_provider_call() -> None:
    llm = FakeStructuredLLM()

    with pytest.raises(PromptParseError):
        build_query_analyst(llm).invoke({"prompt": "  "})

    assert llm.calls == []


def test_specialist_planner_validates_output_and_falls_back() -> None:
    query = ParsedQuery(target_roles=["backend"], skills=["Python"])
    valid_llm = FakeStructuredLLM()
    valid_llm.add(PlannerOutput, PlannerOutput(specialists=[planned()]))
    planned_result = build_specialist_planner(valid_llm, max_specialists=2).invoke(
        {"parsed_query": query}
    )

    failed_llm = FakeStructuredLLM()
    failed_llm.add(PlannerOutput, RuntimeError("provider down"))
    fallback = build_specialist_planner(failed_llm, max_specialists=2).invoke(
        {"parsed_query": query}
    )

    assert planned_result["specs"][0].role_family == "software"
    assert fallback["specs"][0].role_family == "general"


def test_job_scout_refuses_after_budget_exhaustion() -> None:
    provider = FakeProvider()
    graph = build_job_scout(provider)
    shared_budget = budget()
    input_data = {
        "parsed_query": ParsedQuery(target_roles=["engineer"]),
        "budget": shared_budget,
        "page_token": None,
    }

    assert len(graph.invoke(input_data)["page"].candidates) == 1
    assert graph.invoke(input_data)["refusal_reason"] == "budget_exhausted"
    assert provider.calls == 1


def test_page_reader_cache_hit_avoids_second_read_and_charge() -> None:
    reader = FakeReader()
    cache = InMemoryScrapeCache()
    graph = build_page_reader(reader, cache)
    shared_budget = budget(max_firecrawl_calls=2)

    first = graph.invoke({"url": "https://example.com/job", "budget": shared_budget})
    second = graph.invoke({"url": "https://example.com/job", "budget": shared_budget})

    assert first["source"] == "scraped"
    assert second["source"] == "cached"
    assert reader.calls == 1
    assert shared_budget.firecrawl_calls == 1
    assert shared_budget.cache_hits == 1


def test_registry_declares_and_builds_exact_team() -> None:
    assert set(PREDEFINED_SUBAGENTS) == {
        "query_analyst",
        "specialist_planner",
        "job_scout",
        "page_reader",
    }
    assert all(
        definition.input_schema and definition.output_schema
        for definition in PREDEFINED_SUBAGENTS.values()
    )

    llm = FakeStructuredLLM()
    graphs: list[Any] = [
        PREDEFINED_SUBAGENTS["query_analyst"].build(llm),
        PREDEFINED_SUBAGENTS["specialist_planner"].build(llm, max_specialists=1),
        PREDEFINED_SUBAGENTS["job_scout"].build(FakeProvider()),
        PREDEFINED_SUBAGENTS["page_reader"].build(FakeReader(), InMemoryScrapeCache()),
    ]
    assert all(graph.get_graph().nodes for graph in graphs)
