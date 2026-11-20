"""Code-enforced limits for untrusted planner output."""

from tyche_ai.job_search.agents.dynamic.spec import (
    PlannedSpecialistSpec,
    RubricItem,
    SpecialistSpec,
)
from tyche_ai.job_search.models import ParsedQuery

FORBIDDEN_TOOL_WORDS = ("firecrawl", "serpapi", "browser tool", "call tool", "use tool")


class InvalidSpecialistSpec(ValueError):
    pass


def validate_specs(
    planned: list[PlannedSpecialistSpec],
    *,
    max_specialists: int,
) -> list[SpecialistSpec]:
    validated: list[SpecialistSpec] = []
    for index, item in enumerate(planned[:max_specialists], start=1):
        serialized = item.model_dump_json().lower()
        if any(word in serialized for word in FORBIDDEN_TOOL_WORDS):
            raise InvalidSpecialistSpec("Specialist specs cannot request tools")
        total = sum(rubric.weight for rubric in item.rubric)
        if total <= 0:
            raise InvalidSpecialistSpec("Rubric weights must be positive")
        normalized = [
            rubric.model_copy(update={"weight": rubric.weight / total}) for rubric in item.rubric
        ]
        validated.append(
            SpecialistSpec(
                **item.model_dump(exclude={"rubric"}),
                spec_id=f"specialist-{index}",
                rubric=normalized,
            )
        )
    if not validated:
        raise InvalidSpecialistSpec("At least one specialist is required")
    return validated


def default_general_spec(query: ParsedQuery) -> SpecialistSpec:
    role = query.target_roles[0] if query.target_roles else "general"
    return SpecialistSpec(
        spec_id="specialist-1",
        role_family="general",
        persona=f"Hiring screener for {role}"[:200],
        title_keywords=query.target_roles[:8] or query.keywords[:8] or ["job"],
        rubric=[
            RubricItem(name="role", description="Role relevance", weight=0.4),
            RubricItem(name="skills", description="User skill overlap", weight=0.35),
            RubricItem(
                name="constraints", description="Location and work arrangement", weight=0.25
            ),
        ],
        extraction_focus=["tools_software", "certifications"],
        must_have_signals=query.skills[:8],
        deal_breakers=[],
    )
