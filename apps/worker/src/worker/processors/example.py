from datetime import UTC, datetime

from repo_queue import ExampleJob, ExampleJobResult


def process_example_job(payload: object) -> ExampleJobResult:
    ExampleJob.model_validate(payload)
    return ExampleJobResult(processed_at=datetime.now(UTC))
