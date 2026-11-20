"""Idempotent job-search processor independent of Celery and Redis."""

from collections.abc import Callable
from datetime import timedelta

from repo_queue import JobSearchPayload, JobSearchTaskResult
from sqlalchemy.orm import Session
from tyche_ai.job_search.cli import DemoLLM, DemoProvider, DemoReader
from tyche_ai.job_search.graph import run_job_search
from tyche_ai.job_search.graph.context import RunContext
from tyche_ai.job_search.llm import GeminiStructuredLLM, StructuredLLM, TransientLLMError
from tyche_ai.job_search.models import Budget
from tyche_ai.job_search.persistence import DatabaseScrapeCache, JobSearchRepository
from tyche_ai.job_search.settings import JobSearchSettings
from tyche_ai.job_search.tools.firecrawl import FirecrawlPageReader, PageReader
from tyche_ai.job_search.tools.serp import (
    JobSearchProvider,
    PermanentSearchProviderError,
    SerpApiProvider,
    TransientSearchProviderError,
)


class TransientJobSearchError(RuntimeError):
    pass


class PermanentJobSearchError(RuntimeError):
    pass


ContextFactory = Callable[[Session, str], RunContext]


def build_run_context(session: Session, search_id: str) -> RunContext:
    settings = JobSearchSettings()
    llm: StructuredLLM
    provider: JobSearchProvider
    reader: PageReader
    if settings.job_search_fake_mode:
        llm = DemoLLM()
        provider = DemoProvider()
        reader = DemoReader()
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
            raise PermanentJobSearchError(f"Missing provider configuration: {', '.join(missing)}")
        llm = GeminiStructuredLLM(api_key=settings.gemini_api_key, model=settings.llm_model)
        provider = SerpApiProvider(api_key=settings.serpapi_api_key)
        reader = FirecrawlPageReader(api_key=settings.firecrawl_api_key)
    return RunContext(
        search_id=search_id,
        llm=llm,
        provider=provider,
        reader=reader,
        cache=DatabaseScrapeCache(
            session,
            ttl=timedelta(hours=settings.job_search_scrape_cache_ttl_hours),
        ),
        settings=settings,
        budget=Budget(
            max_serp_calls=settings.job_search_max_serp_calls,
            max_firecrawl_calls=settings.job_search_max_firecrawl_calls,
            max_llm_jobs=settings.job_search_max_llm_jobs,
        ),
    )


def process_job_search(
    payload: object,
    session: Session,
    *,
    context_factory: ContextFactory = build_run_context,
) -> JobSearchTaskResult:
    validated = JobSearchPayload.model_validate(payload)
    search_id = str(validated.search_id)
    repository = JobSearchRepository(session)
    search = repository.get(search_id)
    if search is None:
        raise PermanentJobSearchError("Job search does not exist")
    if search.status == "completed":
        return JobSearchTaskResult(search_id=validated.search_id, status="skipped")
    repository.mark_running(search)
    try:
        result = run_job_search(search.prompt, context_factory(session, search_id))
        if result.status == "failed":
            repository.mark_failed(
                search,
                code=result.error_code or "pipeline_failed",
                message=result.error_message or "Pencarian tidak dapat diproses.",
            )
            return JobSearchTaskResult(search_id=validated.search_id, status="failed")
        repository.complete(search, result)
        return JobSearchTaskResult(search_id=validated.search_id, status="completed")
    except (TransientLLMError, TransientSearchProviderError) as error:
        session.rollback()
        raise TransientJobSearchError("A provider is temporarily unavailable") from error
    except PermanentSearchProviderError as error:
        repository.mark_failed(search, code="provider_rejected", message=str(error))
        return JobSearchTaskResult(search_id=validated.search_id, status="failed")
    except PermanentJobSearchError:
        repository.mark_failed(
            search,
            code="configuration",
            message="Konfigurasi penyedia job search belum lengkap.",
        )
        raise
    except Exception as error:
        repository.mark_failed(
            search,
            code="internal_error",
            message="Pencarian gagal karena kesalahan internal.",
        )
        raise PermanentJobSearchError("Job-search processing failed") from error
