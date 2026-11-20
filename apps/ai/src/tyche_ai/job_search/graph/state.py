"""Typed state and reducers for the parent workflow."""

import operator
from typing import Annotated, Literal, TypedDict

from tyche_ai.job_search.agents.dynamic.spec import SpecialistSpec
from tyche_ai.job_search.models import (
    AssessedCandidate,
    Candidate,
    PageContent,
    ParsedQuery,
    PipelineResult,
    RankedJob,
)


class JobSearchInput(TypedDict):
    prompt: str


class JobSearchOutput(TypedDict):
    result: PipelineResult


class JobSearchState(JobSearchInput, total=False):
    status: Literal["running", "completed", "failed"]
    error_code: str
    error_message: str
    parsed_query: ParsedQuery
    specs: list[SpecialistSpec]
    raw_candidates: Annotated[list[Candidate], operator.add]
    candidates: list[Candidate]
    next_page_token: str | None
    page_contents: dict[str, PageContent]
    enrichment: dict[str, Literal["not_needed", "scraped", "cached", "skipped", "failed"]]
    assessed: Annotated[list[AssessedCandidate], operator.add]
    results: list[RankedJob]
    run_log: Annotated[list[dict[str, object]], operator.add]
    result: PipelineResult


class AssessmentDispatch(TypedDict):
    query: ParsedQuery
    candidate: Candidate
    page_content: PageContent | None
    spec: SpecialistSpec
    enrichment_status: Literal["not_needed", "scraped", "cached", "skipped", "failed"]
