from datetime import datetime

from worker.tasks import run_example_job


def test_task_serializes_the_public_result() -> None:
    result = run_example_job.run({"message": "hello"})
    assert set(result) == {"processedAt"}
    assert datetime.fromisoformat(result["processedAt"])
