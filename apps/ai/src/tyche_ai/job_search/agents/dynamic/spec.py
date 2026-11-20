"""Validated data contracts for temporary job specialists."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

RoleFamily = Literal[
    "software",
    "data",
    "product_design",
    "marketing_sales",
    "finance_accounting",
    "operations_logistics",
    "hr_admin",
    "healthcare",
    "education",
    "general",
]
ExtractionFocus = Literal[
    "tech_stack",
    "tools_software",
    "certifications",
    "licenses",
    "languages",
    "shift_schedule",
    "travel_requirement",
    "education_level",
]


class SpecModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RubricItem(SpecModel):
    name: str = Field(min_length=1, max_length=60)
    description: str = Field(min_length=1, max_length=240)
    weight: float = Field(gt=0, le=1)


class PlannedSpecialistSpec(SpecModel):
    role_family: RoleFamily
    persona: str = Field(min_length=1, max_length=200)
    title_keywords: list[str] = Field(min_length=1, max_length=8)
    rubric: list[RubricItem] = Field(min_length=3, max_length=6)
    extraction_focus: list[ExtractionFocus] = Field(default_factory=list, max_length=8)
    must_have_signals: list[str] = Field(default_factory=list, max_length=8)
    deal_breakers: list[str] = Field(default_factory=list, max_length=5)
    thinking_level: Literal["low", "medium"] = "low"
    max_output_tokens: int = Field(default=2_000, ge=256, le=4_000)

    @field_validator("persona", "title_keywords", "must_have_signals", "deal_breakers")
    @classmethod
    def strip_control_characters(cls, value: str | list[str]) -> str | list[str]:
        def clean(item: str) -> str:
            return "".join(character for character in item.strip() if character.isprintable())

        return clean(value) if isinstance(value, str) else [clean(item)[:120] for item in value]


class SpecialistSpec(PlannedSpecialistSpec):
    spec_id: str = Field(pattern=r"^specialist-[1-9]\d*$")


class PlannerOutput(SpecModel):
    specialists: list[PlannedSpecialistSpec] = Field(min_length=1, max_length=6)
