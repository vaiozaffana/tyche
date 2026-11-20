from collections.abc import Generator
from datetime import timedelta
from typing import Any

import pytest
from repo_db import Base, ScrapeCacheEntry, User, create_engine, utc_now
from sqlalchemy import event
from sqlalchemy.orm import Session

from tyche_ai.job_search.models import (
    Candidate,
    JobAssessment,
    PageContent,
    ParsedQuery,
    PipelineResult,
    RankedJob,
)
from tyche_ai.job_search.persistence.db_cache import DatabaseScrapeCache, url_hash
from tyche_ai.job_search.persistence.repository import JobSearchRepository


@pytest.fixture
def database() -> Generator[Session]:
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(_connection: Any, _record: object) -> None:
        _connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(User(id="user-1", name="User", email="user@example.com", image=None))
        session.commit()
        yield session


def pipeline_result(title: str = "Backend Developer") -> PipelineResult:
    return PipelineResult(
        status="completed",
        parsed_query=ParsedQuery(target_roles=["backend developer"]),
        specs=[{"spec_id": "specialist-1"}],
        results=[
            RankedJob(
                candidate=Candidate(
                    title=title,
                    company="Acme",
                    location="Remote",
                    description="Requirements: Python",
                    salary_raw="Rp 15 juta",
                ),
                assessment=JobAssessment(
                    fit_score=90,
                    fit_reason="Strong match",
                    qualifications=["3 years"],
                    tech_stack=["Python"],
                ),
                rank=1,
                specialist_id="specialist-1",
                enrichment_status="not_needed",
            )
        ],
        run_log=[{"event": "done"}],
    )


def test_repository_status_transitions_and_atomic_replacement(database: Session) -> None:
    repository = JobSearchRepository(database)
    search = repository.create(user_id="user-1", prompt="backend jobs")

    repository.mark_running(search)
    repository.complete(search, pipeline_result())

    assert repository.get_owned(search.id, "user-1") is search
    assert repository.get_owned(search.id, "other") is None
    assert search.status == "completed"
    assert repository.list_results(search.id)[0].title == "Backend Developer"

    repository.complete(search, pipeline_result("Python Developer"))

    results = repository.list_results(search.id)
    assert len(results) == 1
    assert results[0].title == "Python Developer"


def test_repository_active_count_and_failure_message_cap(database: Session) -> None:
    repository = JobSearchRepository(database)
    search = repository.create(user_id="user-1", prompt="jobs")

    assert repository.count_active("user-1") == 1
    repository.mark_failed(search, code="provider", message="x" * 700)

    assert repository.count_active("user-1") == 0
    assert search.error_message is not None and len(search.error_message) == 500


def test_database_cache_normalizes_url_and_expires(database: Session) -> None:
    now = utc_now()
    cache = DatabaseScrapeCache(database, ttl=timedelta(hours=24), clock=lambda: now)
    cache.put("HTTPS://Example.com/jobs/1/#fragment", PageContent(status="ok", markdown="Job"))
    database.commit()

    assert cache.get("https://example.com/jobs/1") == PageContent(status="ok", markdown="Job")
    entry = database.get(ScrapeCacheEntry, url_hash("https://example.com/jobs/1"))
    assert entry is not None and entry.url == "https://example.com/jobs/1"

    expired = DatabaseScrapeCache(
        database,
        ttl=timedelta(hours=24),
        clock=lambda: now + timedelta(hours=25),
    )
    assert expired.get("https://example.com/jobs/1") is None
