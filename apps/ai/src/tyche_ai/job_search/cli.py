"""Offline and live command-line entrypoint for the job-search graph."""

import argparse
import sys
from typing import TypeVar

from pydantic import BaseModel

from tyche_ai.job_search.agents.dynamic.spec import PlannedSpecialistSpec, PlannerOutput, RubricItem
from tyche_ai.job_search.graph.builder import run_job_search
from tyche_ai.job_search.graph.context import RunContext
from tyche_ai.job_search.llm import GeminiStructuredLLM, StructuredLLM, ThinkingLevel
from tyche_ai.job_search.models import (
    Budget,
    Candidate,
    JobAssessment,
    PageContent,
    ParsedQuery,
    SearchPage,
)
from tyche_ai.job_search.settings import JobSearchSettings
from tyche_ai.job_search.tools.cache import InMemoryScrapeCache
from tyche_ai.job_search.tools.firecrawl import FirecrawlPageReader, PageReader
from tyche_ai.job_search.tools.serp import JobSearchProvider, SerpApiProvider

T = TypeVar("T", bound=BaseModel)


class DemoLLM:
    def invoke_structured(
        self,
        *,
        system: str,
        user: str,
        schema: type[T],
        thinking_level: ThinkingLevel,
        max_output_tokens: int,
    ) -> T:
        del system, thinking_level, max_output_tokens
        lowered = user.lower()
        value: BaseModel
        if schema is ParsedQuery:
            request = lowered.replace("<user-request>", "").replace("</user-request>", "").strip()
            if request and set(request.split()) == {"asdf"}:
                return schema.model_validate(ParsedQuery())
            finance = any(word in lowered for word in ("akuntan", "accountant", "pajak"))
            value = ParsedQuery(
                target_roles=["tax accountant" if finance else "backend developer"],
                keywords=["brevet", "accurate"] if finance else ["python"],
                locations=["Surabaya"] if "surabaya" in lowered else ["Jakarta"],
                date_posted="week" if "minggu" in lowered or "week" in lowered else None,
                skills=["Brevet A", "Accurate"] if finance else ["Python"],
                language="id"
                if any(word in lowered for word in ("cari", "lowongan", "akuntan"))
                else "en",
            )
        elif schema is PlannerOutput:
            finance = "accountant" in lowered
            value = PlannerOutput(
                specialists=[
                    PlannedSpecialistSpec(
                        role_family="finance_accounting" if finance else "software",
                        persona="Tax accounting hiring screener"
                        if finance
                        else "Backend hiring screener",
                        title_keywords=["accountant", "akuntan"]
                        if finance
                        else ["backend", "developer"],
                        rubric=[
                            RubricItem(name="role", description="Role relevance", weight=0.4),
                            RubricItem(name="skills", description="Skill overlap", weight=0.35),
                            RubricItem(
                                name="constraints", description="Search constraints", weight=0.25
                            ),
                        ],
                        extraction_focus=["certifications", "tools_software"]
                        if finance
                        else ["tech_stack"],
                    )
                ]
            )
        else:
            finance = "accountant" in lowered
            value = JobAssessment(
                fit_score=88 if finance else 90,
                fit_reason="Sesuai profil utama"
                if 'language":"id' in lowered
                else "Strong profile match",
                qualifications=["Relevant experience"],
                tech_stack=[] if finance else ["Python", "PostgreSQL"],
                focus_findings={
                    "certifications": ["Brevet A"],
                    "tools_software": ["Accurate"],
                }
                if finance
                else {"tech_stack": ["Python", "PostgreSQL"]},
                confidence="high",
            )
        return schema.model_validate(value)


class DemoProvider:
    def search(self, query: ParsedQuery, *, page_token: str | None = None) -> SearchPage:
        del page_token
        finance = any("account" in role for role in query.target_roles)
        title = "Tax Accountant" if finance else "Backend Developer"
        return SearchPage(
            candidates=[
                Candidate(
                    title=title,
                    company="Nusantara Demo",
                    location=query.locations[0] if query.locations else "Remote",
                    source_url="https://jobs.example.test/1",
                    source_site="example.test",
                    posted_at="1 day ago",
                    description="Short listing",
                    salary_raw="Rp 10-15 juta",
                ),
                Candidate(
                    title=title,
                    company="Cakrawala Demo",
                    location="Remote",
                    source_url="https://jobs.example.test/2",
                    source_site="example.test",
                    posted_at="3 days ago",
                    description="Requirements " + "relevant experience " * 35,
                ),
            ]
        )


class DemoReader:
    def read(self, url: str) -> PageContent:
        del url
        return PageContent(
            status="ok", markdown="Requirements and qualifications from the full posting."
        )


def _context(
    settings: JobSearchSettings,
    *,
    llm: StructuredLLM,
    provider: JobSearchProvider,
    reader: PageReader,
) -> RunContext:
    return RunContext(
        search_id="cli",
        llm=llm,
        provider=provider,
        reader=reader,
        cache=InMemoryScrapeCache(),
        settings=settings,
        budget=Budget(
            max_serp_calls=settings.job_search_max_serp_calls,
            max_firecrawl_calls=settings.job_search_max_firecrawl_calls,
            max_llm_jobs=settings.job_search_max_llm_jobs,
        ),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a Tyche job search")
    parser.add_argument("prompt")
    parser.add_argument(
        "--fake", action="store_true", help="Use offline fixtures and no provider keys"
    )
    args = parser.parse_args(argv)
    settings = JobSearchSettings()
    fake = args.fake or settings.job_search_fake_mode
    if fake:
        context = _context(settings, llm=DemoLLM(), provider=DemoProvider(), reader=DemoReader())
    else:
        missing = [
            name
            for name, value in (
                ("GEMINI_API_KEY", settings.gemini_api_key),
                ("SERPAPI_API_KEY", settings.serpapi_api_key),
                ("FIRECRAWL_API_KEY", settings.firecrawl_api_key),
            )
            if not value
        ]
        if missing:
            parser.error(f"missing required environment variables: {', '.join(missing)}")
        context = _context(
            settings,
            llm=GeminiStructuredLLM(api_key=settings.gemini_api_key, model=settings.llm_model),
            provider=SerpApiProvider(api_key=settings.serpapi_api_key),
            reader=FirecrawlPageReader(api_key=settings.firecrawl_api_key),
        )
    result = run_job_search(args.prompt, context)
    if result.status == "failed":
        print(f"FAILED: {result.error_message}", file=sys.stderr)
        return 1
    print("RANK  SCORE  TITLE | COMPANY | LOCATION")
    for job in result.results:
        score = "-" if job.assessment.fit_score is None else str(job.assessment.fit_score)
        print(
            f"{job.rank:<5} {score:<6} {job.candidate.title} | "
            f"{job.candidate.company} | {job.candidate.location}"
        )
    print(f"STATS {result.stats.model_dump_json()}")
    print(f"SPECIALISTS {result.specs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
