"""Public API schemas for asynchronous job searches."""

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator

from api.schemas import ApiModel

SearchStatus = Literal["queued", "running", "completed", "failed"]


class JobSearchCreateInput(ApiModel):
    prompt: str = Field(min_length=10, max_length=1_000)

    @field_validator("prompt")
    @classmethod
    def strip_prompt(cls, value: str) -> str:
        if len(value := value.strip()) < 10:
            raise ValueError("Prompt must contain at least 10 characters.")
        return value


class JobSearchCreatedResponse(ApiModel):
    id: str
    status: SearchStatus
    created_at: datetime


class JobSearchSalaryResponse(ApiModel):
    raw: str | None = None
    min: float | None = None
    max: float | None = None
    currency: str | None = None
    period: str | None = None


class JobSearchResultResponse(ApiModel):
    rank: int
    title: str
    company: str
    location: str
    source_url: str | None
    source_site: str | None
    posted_at: str | None
    fit_score: int | None
    fit_reason: str | None
    qualifications: list[str]
    tech_stack: list[str]
    focus_findings: dict[str, list[str]]
    salary: JobSearchSalaryResponse | None
    enrichment: str


class JobSearchDetailResponse(ApiModel):
    id: str
    status: SearchStatus
    prompt: str
    parsed_query: dict[str, object] | None
    specialists: list[dict[str, object]]
    stats: dict[str, object]
    error_message: str | None
    results: list[JobSearchResultResponse]
    created_at: datetime
    completed_at: datetime | None


class JobSearchSummaryResponse(ApiModel):
    id: str
    status: SearchStatus
    prompt: str
    created_at: datetime
    completed_at: datetime | None


class JobSearchListResponse(ApiModel):
    searches: list[JobSearchSummaryResponse]
