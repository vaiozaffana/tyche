from datetime import datetime

import pytest
from pydantic import ValidationError

from worker.processors import process_example_job


def test_processes_validated_job_data() -> None:
    result = process_example_job({"message": " hello "})
    assert isinstance(result.processed_at, datetime)


def test_rejects_invalid_job_data() -> None:
    with pytest.raises(ValidationError):
        process_example_job({"message": 123})


def test_rejects_blank_messages() -> None:
    with pytest.raises(ValidationError):
        process_example_job({"message": "   "})
