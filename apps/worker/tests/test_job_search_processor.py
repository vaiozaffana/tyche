from collections.abc import Generator
from datetime import timedelta
from typing import Any

import pytest
from repo_db import Base, User, create_engine
from sqlalchemy import event
from sqlalchemy.orm import Session
from tyche_ai.job_search.cli import DemoLLM, DemoProvider, DemoReader
from tyche_ai.job_search.graph.context import RunContext
from tyche_ai.job_search.llm import FakeStructuredLLM, StructuredLLM
from tyche_ai.job_search.models import Budget, PageContent, ParsedQuery, SearchPage
from tyche_ai.job_search.persistence import DatabaseScrapeCache, JobSearchRepository
from tyche_ai.job_search.settings import JobSearchSettings
from tyche_ai.job_search.tools.firecrawl import PageReader
from tyche_ai.job_search.tools.serp import JobSearchProvider, TransientSearchProviderError

from worker.processors.job_search_processor import (
    ContextFactory,
    TransientJobSearchError,
    process_job_search,
)


@pytest.fixture
def database() -> Generator[Session]:
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection: Any, _record: object) -> None:
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(User(id="user-1", name="User", email="user@example.com", image=None))
        session.commit()
        yield session


class FailedReader:
    def read(self, url: str) -> PageContent:
        del url
        return PageContent(status="failed", error="blocked")


class TransientProvider:
    def search(self, query: ParsedQuery, *, page_token: str | None = None) -> SearchPage:
        del query, page_token
        raise TransientSearchProviderError("temporary")


def context_factory(
    *,
    llm: StructuredLLM | None = None,
    provider: JobSearchProvider | None = None,
    reader: PageReader | None = None,
) -> ContextFactory:
    def build(session: Session, search_id: str) -> RunContext:
        settings = JobSearchSettings(
            job_search_fake_mode=True,
            job_search_max_serp_calls=1,
            job_search_max_firecrawl_calls=2,
            job_search_max_llm_jobs=5,
        )
        return RunContext(
            search_id=search_id,
            llm=llm or DemoLLM(),
            provider=provider or DemoProvider(),
            reader=reader or DemoReader(),
            cache=DatabaseScrapeCache(session, ttl=timedelta(hours=24)),
            settings=settings,
            budget=Budget(max_serp_calls=1, max_firecrawl_calls=2, max_llm_jobs=5),
        )

    return build


def test_processor_persists_results_and_is_idempotent(database: Session) -> None:
    repository = JobSearchRepository(database)
    search = repository.create(user_id="user-1", prompt="backend Python jobs")
    payload = {"search_id": search.id}

    result = process_job_search(payload, database, context_factory=context_factory())
    repeated = process_job_search(payload, database, context_factory=context_factory())

    assert result.status == "completed"
    assert repeated.status == "skipped"
    assert search.status == "completed"
    assert [row.rank for row in repository.list_results(search.id)] == [1, 2]


def test_parse_failure_marks_failed_without_provider_call(database: Session) -> None:
    repository = JobSearchRepository(database)
    search = repository.create(user_id="user-1", prompt="asdf")
    llm = FakeStructuredLLM()
    llm.add(ParsedQuery, ParsedQuery(), ParsedQuery())

    result = process_job_search(
        {"search_id": search.id},
        database,
        context_factory=context_factory(llm=llm),
    )

    assert result.status == "failed"
    assert search.status == "failed"
    assert search.error_code == "prompt_parse"


def test_firecrawl_failure_still_completes(database: Session) -> None:
    repository = JobSearchRepository(database)
    search = repository.create(user_id="user-1", prompt="backend jobs")

    result = process_job_search(
        {"search_id": search.id},
        database,
        context_factory=context_factory(reader=FailedReader()),
    )

    assert result.status == "completed"
    assert repository.list_results(search.id)[0].enrichment_status == "failed"


def test_transient_provider_error_is_raised_for_celery_retry(database: Session) -> None:
    search = JobSearchRepository(database).create(user_id="user-1", prompt="backend jobs")

    with pytest.raises(TransientJobSearchError):
        process_job_search(
            {"search_id": search.id},
            database,
            context_factory=context_factory(provider=TransientProvider()),
        )

    assert search.status == "running"
