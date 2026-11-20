from uuid import uuid4

import pytest
from celery import Celery
from pydantic import ValidationError

from repo_queue import JOB_SEARCH_TASK_NAME, JobSearchPayload, enqueue_job_search


def test_payload_is_json_safe_and_rejects_unknown_fields() -> None:
    search_id = uuid4()

    assert JobSearchPayload(search_id=search_id).model_dump(mode="json") == {
        "search_id": str(search_id)
    }
    with pytest.raises(ValidationError):
        JobSearchPayload.model_validate({"search_id": str(search_id), "prompt": "secret"})


def test_producer_sends_only_validated_id(monkeypatch: pytest.MonkeyPatch) -> None:
    app = Celery("test")
    search_id = str(uuid4())
    sent: dict[str, object] = {}

    def fake_send_task(name: str, **kwargs: object) -> object:
        sent.update(name=name, **kwargs)
        return object()

    monkeypatch.setattr(app, "send_task", fake_send_task)

    enqueue_job_search(app, search_id)

    assert sent == {
        "name": JOB_SEARCH_TASK_NAME,
        "kwargs": {"payload": {"search_id": search_id}},
    }
