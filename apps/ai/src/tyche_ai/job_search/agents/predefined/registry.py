"""Registry proving the predefined subagent team is known at build time."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from langgraph.graph.state import CompiledStateGraph

from tyche_ai.job_search.agents.predefined.job_scout import (
    JobScoutInput,
    JobScoutOutput,
    build_job_scout,
)
from tyche_ai.job_search.agents.predefined.page_reader import (
    PageReaderInput,
    PageReaderOutput,
    build_page_reader,
)
from tyche_ai.job_search.agents.predefined.query_analyst import (
    QueryAnalystInput,
    QueryAnalystOutput,
    build_query_analyst,
)
from tyche_ai.job_search.agents.predefined.specialist_planner import (
    SpecialistPlannerInput,
    SpecialistPlannerOutput,
    build_specialist_planner,
)

Builder = Callable[..., CompiledStateGraph[Any, Any, Any, Any]]


@dataclass(frozen=True, slots=True)
class SubagentDefinition:
    name: str
    description: str
    input_schema: type[Any]
    output_schema: type[Any]
    build: Builder


PREDEFINED_SUBAGENTS = {
    "query_analyst": SubagentDefinition(
        "query_analyst",
        "Parse bilingual free-form job searches",
        QueryAnalystInput,
        QueryAnalystOutput,
        build_query_analyst,
    ),
    "specialist_planner": SubagentDefinition(
        "specialist_planner",
        "Plan guarded runtime specialist specs",
        SpecialistPlannerInput,
        SpecialistPlannerOutput,
        build_specialist_planner,
    ),
    "job_scout": SubagentDefinition(
        "job_scout",
        "Discover jobs within the SerpApi budget",
        JobScoutInput,
        JobScoutOutput,
        build_job_scout,
    ),
    "page_reader": SubagentDefinition(
        "page_reader",
        "Read individual postings cache-first",
        PageReaderInput,
        PageReaderOutput,
        build_page_reader,
    ),
}
