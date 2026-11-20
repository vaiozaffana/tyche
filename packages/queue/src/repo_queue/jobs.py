"""Validated producer helpers."""

from celery import Celery
from celery.result import AsyncResult

from repo_queue.contracts import JOB_SEARCH_TASK_NAME, JobSearchPayload


def enqueue_job_search(app: Celery, search_id: str) -> AsyncResult:
    payload = JobSearchPayload.model_validate({"search_id": search_id})
    return app.send_task(
        JOB_SEARCH_TASK_NAME,
        kwargs={"payload": payload.model_dump(mode="json")},
    )
