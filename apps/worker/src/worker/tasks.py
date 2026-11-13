from repo_queue import EXAMPLE_TASK_NAME

from worker.app import celery_app
from worker.processors import process_example_job


@celery_app.task(name=EXAMPLE_TASK_NAME)  # type: ignore[untyped-decorator]
def run_example_job(payload: object) -> dict[str, str]:
    result = process_example_job(payload)
    return result.model_dump(mode="json", by_alias=True)
