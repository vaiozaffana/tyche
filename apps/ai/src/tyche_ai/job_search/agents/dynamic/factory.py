"""Dynamic specialist compilation and deterministic routing."""

import re
from typing import Any

from langgraph.graph.state import CompiledStateGraph

from tyche_ai.job_search.agents.dynamic.job_assessor import build_assessor
from tyche_ai.job_search.agents.dynamic.spec import SpecialistSpec
from tyche_ai.job_search.llm import StructuredLLM
from tyche_ai.job_search.models import Candidate


def build_specialist(
    spec: SpecialistSpec,
    llm: StructuredLLM,
) -> CompiledStateGraph[Any, Any, Any, Any]:
    return build_assessor(spec, llm)


def route_candidate(candidate: Candidate, specs: list[SpecialistSpec]) -> SpecialistSpec:
    if not specs:
        raise ValueError("At least one specialist is required")
    title = set(re.findall(r"\w+", candidate.title.lower()))
    for spec in specs:
        keywords = set(re.findall(r"\w+", " ".join(spec.title_keywords).lower()))
        if title & keywords:
            return spec
    return next((spec for spec in specs if spec.role_family == "general"), specs[0])
