"""Deterministic gate for expensive page reads."""

from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse

from tyche_ai.job_search.models import Budget, Candidate, ParsedQuery
from tyche_ai.job_search.screening.title_filter import title_matches

DESCRIPTION_MARKERS = (
    "kualifikasi",
    "persyaratan",
    "requirements",
    "qualifications",
    "responsibilities",
    "tanggung jawab",
    "gaji",
    "salary",
)
GateReason = Literal[
    "no_url",
    "title_mismatch",
    "description_sufficient",
    "domain_blocked",
    "budget_exhausted",
    "needs_scrape",
]


@dataclass(frozen=True, slots=True)
class GateSettings:
    min_description_chars: int = 500
    title_match_threshold: float = 0.5
    blocked_domains: tuple[str, ...] = ("linkedin.com",)


@dataclass(frozen=True, slots=True)
class GateDecision:
    scrape: bool
    reason: GateReason


def decide(
    candidate: Candidate,
    query: ParsedQuery,
    settings: GateSettings,
    budget: Budget,
    cache_state: Literal["hit", "miss"] = "miss",
) -> GateDecision:
    del cache_state
    if not candidate.source_url:
        return GateDecision(False, "no_url")
    if not title_matches(candidate, query, threshold=settings.title_match_threshold)[0]:
        return GateDecision(False, "title_mismatch")
    lowered = candidate.description.lower()
    description_incomplete = len(candidate.description) < settings.min_description_chars or not (
        candidate.highlights or any(marker in lowered for marker in DESCRIPTION_MARKERS)
    )
    if not description_incomplete:
        return GateDecision(False, "description_sufficient")
    host = urlparse(candidate.source_url).hostname or ""
    if any(host == domain or host.endswith(f".{domain}") for domain in settings.blocked_domains):
        return GateDecision(False, "domain_blocked")
    if budget.firecrawl_calls >= budget.max_firecrawl_calls:
        return GateDecision(False, "budget_exhausted")
    return GateDecision(True, "needs_scrape")
