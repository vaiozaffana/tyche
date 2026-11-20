"""Thin Celery registration for job-search processing."""

from typing import Any

from repo_db import create_engine, create_session_factory
from repo_queue import JOB_SEARCH_TASK_NAME

from worker.app import celery_app
from worker.processors.job_search_processor import TransientJobSearchError, process_job_search
from worker.settings import Settings


@celery_app.task(
    name=JOB_SEARCH_TASK_NAME,
    autoretry_for=(TransientJobSearchError,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)  # type: ignore[untyped-decorator]
def run_job_search_task(payload: object) -> dict[str, Any]:
    engine = create_engine(Settings().database_url)
    try:
        with create_session_factory(engine)() as session:
            return process_job_search(payload, session).model_dump(mode="json")
    finally:
        engine.dispose()
