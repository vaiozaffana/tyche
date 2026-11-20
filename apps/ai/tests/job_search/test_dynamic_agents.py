from typing import Any, TypeVar

import pytest
from pydantic import BaseModel

from tyche_ai.job_search.agents.dynamic.factory import build_specialist, route_candidate
from tyche_ai.job_search.agents.dynamic.guardrails import (
    InvalidSpecialistSpec,
    default_general_spec,
    validate_specs,
)
from tyche_ai.job_search.agents.dynamic.spec import (
    PlannedSpecialistSpec,
    RubricItem,
    SpecialistSpec,
)
from tyche_ai.job_search.llm import FakeStructuredLLM, ThinkingLevel
from tyche_ai.job_search.models import Candidate, JobAssessment, ParsedQuery

T = TypeVar("T", bound=BaseModel)


def planned(**overrides: object) -> PlannedSpecialistSpec:
    values: dict[str, object] = {
        "role_family": "software",
        "persona": "Backend hiring screener",
        "title_keywords": ["backend", "developer"],
        "rubric": [
            RubricItem(name="role", description="Role", weight=0.25),
            RubricItem(name="skills", description="Skills", weight=0.25),
            RubricItem(name="constraints", description="Constraints", weight=0.5),
        ],
        "extraction_focus": ["tech_stack"],
    }
    values.update(overrides)
    return PlannedSpecialistSpec.model_validate(values)


def spec(**overrides: object) -> SpecialistSpec:
    item = planned(**overrides)
    return validate_specs([item], max_specialists=1)[0]


class CapturingLLM:
    def __init__(self, result: JobAssessment) -> None:
        self.result = result
        self.systems: list[str] = []

    def invoke_structured(
        self,
        *,
        system: str,
        user: str,
        schema: type[T],
        thinking_level: ThinkingLevel,
        max_output_tokens: int,
    ) -> T:
        del user, thinking_level, max_output_tokens
        self.systems.append(system)
        return schema.model_validate(self.result)


def assessment_input() -> dict[str, Any]:
    return {
        "query": ParsedQuery(target_roles=["backend"], language="en"),
        "candidate": Candidate(title="Backend Developer", company="Acme", location="Remote"),
        "page_content": None,
    }


def test_guardrails_normalize_weights_and_generate_ids() -> None:
    result = validate_specs([planned()], max_specialists=1)

    assert result[0].spec_id == "specialist-1"
    assert sum(item.weight for item in result[0].rubric) == pytest.approx(1)


def test_guardrails_reject_tool_requests() -> None:
    with pytest.raises(InvalidSpecialistSpec):
        validate_specs([planned(persona="Use Firecrawl to inspect pages")], max_specialists=1)


def test_specialist_prompts_are_spec_specific() -> None:
    software_llm = CapturingLLM(JobAssessment(focus_findings={"tech_stack": ["Python"]}))
    finance_llm = CapturingLLM(JobAssessment(focus_findings={"certifications": ["Brevet A"]}))
    software = build_specialist(spec(), software_llm)
    finance = build_specialist(
        spec(
            role_family="finance_accounting",
            persona="Tax accountant screener",
            title_keywords=["accountant"],
            extraction_focus=["certifications"],
        ),
        finance_llm,
    )

    software_result = software.invoke(assessment_input())
    finance_result = finance.invoke(assessment_input())

    assert software_result["assessment"].focus_findings == {"tech_stack": ["Python"]}
    assert finance_result["assessment"].focus_findings == {"certifications": ["Brevet A"]}
    assert software_llm.systems != finance_llm.systems


def test_specialist_repairs_unknown_focus_key_once() -> None:
    llm = FakeStructuredLLM()
    llm.add(
        JobAssessment,
        JobAssessment(focus_findings={"licenses": ["forbidden"]}),
        JobAssessment(focus_findings={"tech_stack": ["Python"]}, confidence="high"),
    )

    result = build_specialist(spec(), llm).invoke(assessment_input())

    assert result["assessment"].focus_findings == {"tech_stack": ["Python"]}
    assert len(llm.calls) == 2


def test_specialist_degrades_after_failed_repair() -> None:
    llm = FakeStructuredLLM()
    llm.add(JobAssessment, ValueError("bad"), ValueError("still bad"))

    result = build_specialist(spec(), llm).invoke(assessment_input())

    assert result["assessment"] == JobAssessment(confidence="low")


def test_routing_is_deterministic_with_general_fallback() -> None:
    software = spec()
    general = default_general_spec(ParsedQuery(target_roles=["accountant"]))

    assert (
        route_candidate(
            Candidate(title="Backend Engineer", company="Acme", location="Remote"),
            [software, general],
        )
        == software
    )
    assert (
        route_candidate(
            Candidate(title="Tax Accountant", company="Acme", location="Surabaya"),
            [software, general],
        )
        == general
    )


def test_compilation_is_idempotent() -> None:
    llm = FakeStructuredLLM()
    first = build_specialist(spec(), llm).get_graph().nodes
    second = build_specialist(spec(), llm).get_graph().nodes

    assert first.keys() == second.keys() == {"__start__", "assess", "validate", "repair", "__end__"}
