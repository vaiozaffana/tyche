from collections.abc import AsyncIterator, Iterator

import pytest
from httpx import ASGITransport, AsyncClient
from repo_db import Base, create_engine, create_session_factory
from sqlalchemy import Engine

from api import create_app
from api.settings import Settings


@pytest.fixture
def engine() -> Iterator[Engine]:
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def anyio_backend() -> tuple[str, dict[str, bool]]:
    return "asyncio", {"use_uvloop": True}


@pytest.fixture
async def client(engine: Engine) -> AsyncIterator[AsyncClient]:
    app = create_app(
        Settings(NODE_ENV="test", DATABASE_URL="sqlite:///:memory:"),
        create_session_factory(engine),
    )
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as test_client,
    ):
        yield test_client
