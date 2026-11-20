"""Stage-1-only live coverage probe for SerpApi Google Jobs."""

from collections import Counter
from dataclasses import dataclass

from tyche_ai.job_search.models import Candidate, ParsedQuery
from tyche_ai.job_search.settings import JobSearchSettings
from tyche_ai.job_search.tools.serp import JobSearchProvider, SearchProviderError, SerpApiProvider

PROBE_QUERIES = (
    ParsedQuery(target_roles=["backend developer"], keywords=["Python"], locations=["Jakarta"]),
    ParsedQuery(target_roles=["frontend developer"], keywords=["React"], locations=["Bandung"]),
    ParsedQuery(target_roles=["mobile developer"], keywords=["Flutter"], locations=["Surabaya"]),
    ParsedQuery(target_roles=["data analyst"], keywords=["SQL"], locations=["Jakarta"]),
    ParsedQuery(target_roles=["data engineer"], keywords=["Python"], locations=["Remote"]),
    ParsedQuery(target_roles=["product designer"], keywords=["Figma"], locations=["Jakarta"]),
    ParsedQuery(target_roles=["digital marketing"], locations=["Bandung"]),
    ParsedQuery(target_roles=["sales executive"], locations=["Surabaya"]),
    ParsedQuery(target_roles=["tax accountant"], keywords=["Brevet"], locations=["Surabaya"]),
    ParsedQuery(target_roles=["finance analyst"], locations=["Jakarta"]),
    ParsedQuery(target_roles=["warehouse supervisor"], locations=["Bekasi"]),
    ParsedQuery(target_roles=["human resources"], locations=["Jakarta"]),
    ParsedQuery(target_roles=["registered nurse"], locations=["Bandung"]),
    ParsedQuery(target_roles=["English teacher"], locations=["Remote"]),
    ParsedQuery(target_roles=["operations manager"], locations=["Remote"], date_posted="week"),
)


@dataclass(frozen=True, slots=True)
class ProbeSummary:
    counts: list[int]
    source_counts: Counter[str]
    short_descriptions: int
    total_candidates: int


def _source(candidate: Candidate) -> str:
    site = (candidate.source_site or "other").lower()
    return next(
        (name for name in ("linkedin", "jobstreet", "glints", "dealls") if name in site),
        "other",
    )


def run_probe(provider: JobSearchProvider) -> ProbeSummary:
    counts = []
    sources: Counter[str] = Counter()
    short = 0
    total = 0
    for query in PROBE_QUERIES:
        candidates = provider.search(query).candidates
        counts.append(len(candidates))
        total += len(candidates)
        for candidate in candidates:
            sources[_source(candidate)] += 1
            short += len(candidate.description) < 500
    return ProbeSummary(counts, sources, short, total)


def main() -> int:
    settings = JobSearchSettings()
    if not settings.serpapi_api_key:
        print("SKIPPED: SERPAPI_API_KEY is not configured; no live coverage claim was made.")
        return 0
    try:
        summary = run_probe(SerpApiProvider(api_key=settings.serpapi_api_key))
    except SearchProviderError:
        print("FAILED: SerpApi rejected the probe; no live coverage claim was made.")
        return 1
    print("QUERY  RESULTS")
    for index, count in enumerate(summary.counts, start=1):
        print(f"{index:>5}  {count:>7}")
    short_share = (
        summary.short_descriptions / summary.total_candidates if summary.total_candidates else 0
    )
    print(f"SOURCES {dict(summary.source_counts)}")
    print(f"SHORT_DESCRIPTION_SHARE {short_share:.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
