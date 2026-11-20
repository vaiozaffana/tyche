import pytest
from pydantic import ValidationError

from worker.settings import Settings


def test_worker_uses_local_redis_by_default() -> None:
    assert Settings.model_construct().redis_url == "redis://localhost:16379/0"


def test_worker_rejects_non_redis_urls() -> None:
    with pytest.raises(ValidationError):
        Settings(REDIS_URL="http://localhost:6379")


def test_worker_rejects_unsupported_database_urls() -> None:
    with pytest.raises(ValidationError):
        Settings(DATABASE_URL="mysql://localhost/tyche")
