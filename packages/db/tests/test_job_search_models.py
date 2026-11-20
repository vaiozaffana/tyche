from collections.abc import Generator
from typing import Any

import pytest
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from repo_db import Base, JobSearch, JobSearchResult, User, create_engine


@pytest.fixture
def database() -> Generator[Session]:
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(_connection: Any, _record: object) -> None:
        _connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(User(id="user-1", name="User", email="user@example.com", image=None))
        session.commit()
        yield session


def test_sqlmodel_tables_share_base_metadata_and_cascade(database: Session) -> None:
    search = JobSearch(user_id="user-1", prompt="backend jobs")
    database.add(search)
    database.flush()
    result = JobSearchResult(
        search_id=search.id,
        rank=1,
        title="Backend Developer",
        company="Acme",
        location="Remote",
        specialist_id="specialist-1",
        enrichment_status="not_needed",
    )
    database.add(result)
    database.commit()
    result_id = result.id

    database.delete(search)
    database.commit()

    assert database.get(JobSearchResult, result_id) is None


def test_database_rejects_invalid_search_status(database: Session) -> None:
    database.add(JobSearch(user_id="user-1", prompt="jobs", status="unknown"))

    with pytest.raises(IntegrityError):
        database.commit()

    database.rollback()
