from collections.abc import Sequence

from celery import Celery
from celery.result import AsyncResult

from repo_queue.contracts import EXAMPLE_TASK_NAME, ExampleJob


def create_celery(redis_url: str, *, include: Sequence[str] = ()) -> Celery:
    app = Celery(
        "monorepo_template",
        broker=redis_url,
        backend=redis_url,
        include=list(include),
    )
    app.conf.update(
        accept_content=["json"],
        broker_connection_retry_on_startup=True,
        result_serializer="json",
        task_serializer="json",
        timezone="UTC",
    )
    return app


def enqueue_example_job(app: Celery, input: ExampleJob) -> AsyncResult:
    payload = ExampleJob.model_validate(input).model_dump()
    return app.send_task(EXAMPLE_TASK_NAME, kwargs={"payload": payload})
