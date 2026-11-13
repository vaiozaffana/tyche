from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from repo_db import User, create_session_factory
from sqlalchemy import Engine

from api.modules.auth.service import register_user

pytestmark = pytest.mark.anyio


async def test_health_does_not_require_a_database(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True, "service": "api"}


async def test_register_session_profile_and_logout(client: AsyncClient) -> None:
    registered = await client.post(
        "/api/auth/sign-up/email",
        json={"name": " User ", "email": "USER@example.com", "password": "password123"},
    )
    assert registered.status_code == 200
    assert registered.json()["user"]["email"] == "user@example.com"
    assert registered.json()["user"]["createdAt"].endswith("Z")
    assert registered.json()["user"]["updatedAt"].endswith("Z")
    assert registered.cookies.get("session")

    duplicate = await client.post(
        "/api/auth/sign-up/email",
        json={"name": "User", "email": "USER@example.com", "password": "password123"},
    )
    assert duplicate.status_code == 400
    assert duplicate.json() == {"detail": "Email is already registered."}

    session = await client.get("/session")
    assert session.status_code == 200
    assert session.json()["user"]["name"] == "User"
    assert session.json()["session"]["expiresAt"].endswith("Z")

    updated = await client.patch("/profile", json={"name": "Updated", "image": ""})
    assert updated.status_code == 200
    assert updated.json()["user"]["image"] is None

    assert (await client.post("/api/auth/sign-out")).status_code == 200
    assert (await client.get("/session")).json() == {"error": "unauthorized"}


async def test_login_rejects_invalid_credentials(client: AsyncClient) -> None:
    response = await client.post(
        "/api/auth/sign-in/email",
        json={"email": "missing@example.com", "password": "wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password."}


async def test_banned_user_cannot_login_or_keep_a_session(
    client: AsyncClient, engine: Engine
) -> None:
    registered = await client.post(
        "/api/auth/sign-up/email",
        json={"name": "Banned", "email": "banned@example.com", "password": "password123"},
    )
    assert registered.status_code == 200

    with create_session_factory(engine)() as database:
        user = database.get(User, registered.json()["user"]["id"])
        assert user is not None
        user.banned = True
        database.commit()

    assert (await client.get("/session")).status_code == 401
    login = await client.post(
        "/api/auth/sign-in/email",
        json={"email": "banned@example.com", "password": "password123"},
    )
    assert login.status_code == 401


async def test_validation_and_origins(client: AsyncClient) -> None:
    invalid = await client.post(
        "/api/auth/sign-up/email",
        json={"name": "", "email": "bad", "password": "short"},
    )
    assert invalid.status_code == 400
    assert invalid.json() == {"error": "validation_error"}

    forbidden = await client.post(
        "/api/auth/sign-up/email",
        headers={"Origin": "https://evil.example"},
        json={"name": "User", "email": "user@example.com", "password": "password123"},
    )
    assert forbidden.status_code == 403
    assert forbidden.json() == {"error": "forbidden"}


async def test_admin_user_pagination_and_invalid_cursor(
    client: AsyncClient, engine: Engine
) -> None:
    factory = create_session_factory(engine)
    with factory() as database:
        register_user(
            database,
            email="admin@example.com",
            name="Admin",
            password="password123",
            role="admin",
        )
        created_at = datetime(2026, 7, 3, tzinfo=UTC).replace(tzinfo=None)
        database.add_all(
            [
                User(
                    id=f"user-{index}",
                    email=f"user-{index}@example.com",
                    name=f"User {index}",
                    role="user",
                    created_at=created_at,
                    updated_at=created_at,
                )
                for index in range(1, 4)
            ]
        )
        database.commit()

    login = await client.post(
        "/api/auth/sign-in/email",
        json={"email": "admin@example.com", "password": "password123"},
    )
    assert login.status_code == 200
    first = await client.get("/users?limit=2")
    assert first.status_code == 200
    assert len(first.json()["users"]) == 2
    assert first.json()["nextCursor"]
    second = await client.get(f"/users?limit=2&cursor={first.json()['nextCursor']}")
    assert second.status_code == 200
    assert not set(user["id"] for user in first.json()["users"]) & set(
        user["id"] for user in second.json()["users"]
    )
    assert (await client.get("/users?cursor=missing")).json() == {"error": "invalid_cursor"}


async def test_users_requires_admin(client: AsyncClient) -> None:
    assert (await client.get("/users")).json() == {"error": "unauthorized"}
    await client.post(
        "/api/auth/sign-up/email",
        json={"name": "User", "email": "user@example.com", "password": "password123"},
    )
    assert (await client.get("/users")).json() == {"error": "forbidden"}
