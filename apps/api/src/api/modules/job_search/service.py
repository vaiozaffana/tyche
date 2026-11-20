"""Database and queue operations for the job-search API."""

from celery import Celery
from repo_db import JobSearch, JobSearchResult
from repo_queue import enqueue_job_search
from sqlalchemy.orm import Session
from tyche_ai.job_search.persistence import JobSearchRepository


class TooManyActiveSearchesError(ValueError):
    pass


class QueueUnavailableError(RuntimeError):
    pass


def create_search(
    database: Session,
    queue: Celery,
    *,
    user_id: str,
    prompt: str,
    max_active: int,
) -> JobSearch:
    repository = JobSearchRepository(database)
    if repository.count_active(user_id) >= max_active:
        raise TooManyActiveSearchesError
    search = repository.create(user_id=user_id, prompt=prompt)
    try:
        enqueue_job_search(queue, search.id)
    except Exception as error:
        repository.mark_failed(
            search,
            code="queue_unavailable",
            message="Pencarian tidak dapat dimasukkan ke antrean.",
        )
        raise QueueUnavailableError from error
    return search


def load_search(
    database: Session,
    *,
    search_id: str,
    user_id: str,
) -> tuple[JobSearch, list[JobSearchResult]] | None:
    repository = JobSearchRepository(database)
    search = repository.get_owned(search_id, user_id)
    if search is None:
        return None
    return search, repository.list_results(search.id)


def list_searches(database: Session, *, user_id: str) -> list[JobSearch]:
    return JobSearchRepository(database).list_recent(user_id)
