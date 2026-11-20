"""Budgeted SerpApi subgraph."""

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from tyche_ai.job_search.models import Budget, ParsedQuery, SearchPage
from tyche_ai.job_search.tools.serp import JobSearchProvider


class JobScoutInput(TypedDict):
    parsed_query: ParsedQuery
    budget: Budget
    page_token: str | None


class JobScoutOutput(TypedDict):
    page: SearchPage
    refusal_reason: str | None


def build_job_scout(provider: JobSearchProvider) -> CompiledStateGraph[Any, Any, Any, Any]:
    def search(state: JobScoutInput) -> JobScoutOutput:
        if not state["budget"].take_serp():
            return {"page": SearchPage(), "refusal_reason": "budget_exhausted"}
        return {
            "page": provider.search(state["parsed_query"], page_token=state["page_token"]),
            "refusal_reason": None,
        }

    graph = StateGraph(JobScoutOutput, input_schema=JobScoutInput, output_schema=JobScoutOutput)
    graph.add_node("search", search)
    graph.add_edge(START, "search")
    graph.add_edge("search", END)
    return graph.compile(name="job_scout")
