"""Typed boundaries shared by the job-search graph."""

from dataclasses import dataclass, field
from threading import Lock
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class JobSearchModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ParsedQuery(JobSearchModel):
    target_roles: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    remote_preference: Literal["remote", "hybrid", "onsite", "any"] = "any"
    date_posted: Literal["today", "3days", "week", "month"] | None = None
    skills: list[str] = Field(default_factory=list)
    experience_level: str | None = None
    language: Literal["id", "en"] = "id"


class Candidate(JobSearchModel):
    external_id: str | None = None
    title: str
    company: str
    location: str
    source_url: str | None = None
    source_site: str | None = None
    posted_at: str | None = None
    description: str = ""
    highlights: list[str] = Field(default_factory=list)
    salary_raw: str | None = None


class SearchPage(JobSearchModel):
    candidates: list[Candidate] = Field(default_factory=list)
    next_page_token: str | None = None


class PageContent(JobSearchModel):
    markdown: str = ""
    status: Literal["ok", "failed", "blocked"]
    error: str | None = None


class Salary(JobSearchModel):
    raw: str | None = None
    min: float | None = None
    max: float | None = None
    currency: str | None = None
    period: str | None = None


class JobAssessment(JobSearchModel):
    fit_score: int | None = Field(default=None, ge=0, le=100)
    fit_reason: str | None = None
    qualifications: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)
    focus_findings: dict[str, list[str]] = Field(default_factory=dict)
    salary: Salary | None = None
    experience_years: float | None = Field(default=None, ge=0)
    work_arrangement: str | None = None
    deal_breaker_hits: list[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "low"


class RankedJob(JobSearchModel):
    candidate: Candidate
    assessment: JobAssessment
    rank: int = Field(ge=1)
    specialist_id: str
    enrichment_status: Literal["not_needed", "scraped", "cached", "skipped", "failed"]


class AssessedCandidate(JobSearchModel):
    candidate: Candidate
    assessment: JobAssessment
    specialist_id: str
    enrichment_status: Literal["not_needed", "scraped", "cached", "skipped", "failed"]


class PipelineStats(JobSearchModel):
    serp_calls: int = 0
    candidates: int = 0
    after_dedup: int = 0
    after_filter: int = 0
    firecrawl_calls: int = 0
    cache_hits: int = 0
    llm_calls: int = 0
    specialists: int = 0


class PipelineResult(JobSearchModel):
    status: Literal["completed", "failed"]
    parsed_query: ParsedQuery | None = None
    specs: list[dict[str, object]] = Field(default_factory=list)
    results: list[RankedJob] = Field(default_factory=list)
    stats: PipelineStats = Field(default_factory=PipelineStats)
    run_log: list[dict[str, object]] = Field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None


@dataclass(slots=True)
class Budget:
    max_serp_calls: int
    max_firecrawl_calls: int
    max_llm_jobs: int
    serp_calls: int = 0
    firecrawl_calls: int = 0
    llm_calls: int = 0
    cache_hits: int = 0
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def _take(
        self, counter: Literal["serp_calls", "firecrawl_calls", "llm_calls"], limit: int
    ) -> bool:
        with self._lock:
            current = getattr(self, counter)
            if current >= limit:
                return False
            setattr(self, counter, current + 1)
            return True

    def take_serp(self) -> bool:
        return self._take("serp_calls", self.max_serp_calls)

    def take_firecrawl(self) -> bool:
        return self._take("firecrawl_calls", self.max_firecrawl_calls)

    def take_llm(self) -> bool:
        return self._take("llm_calls", self.max_llm_jobs)

    def record_cache_hit(self) -> None:
        with self._lock:
            self.cache_hits += 1
