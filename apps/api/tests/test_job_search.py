from typing import Any, cast

import pytest
from httpx import AsyncClient
from repo_db import JobSearch, JobSearchResult, create_session_factory
from sqlalchemy import Engine, select

from api.modules.job_search import service

pytestmark = pytest.mark.anyio


async def register(client: AsyncClient, email: str) -> dict[str, Any]:
    response = await client.post(
        "/api/auth/sign-up/email",
        json={"name": "User", "email": email, "password": "password123"},
    )
    assert response.status_code == 200
    return cast(dict[str, Any], response.json()["user"])


def allow_enqueue(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(service, "enqueue_job_search", lambda _queue, _search_id: object())


async def test_job_search_endpoints_require_auth(client: AsyncClient) -> None:
    assert (
        await client.post("/job-searches", json={"prompt": "backend developer"})
    ).status_code == 401
    assert (await client.get("/job-searches")).status_code == 401
    assert (await client.get("/job-searches/missing")).status_code == 401


async def test_create_poll_completed_shape_and_list(
    client: AsyncClient,
    engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    allow_enqueue(monkeypatch)
    await register(client, "owner@example.com")

    created = await client.post(
        "/job-searches",
        json={"prompt": "  backend developer Python Jakarta  "},
    )

    assert created.status_code == 202
    assert created.json()["status"] == "queued"
    assert created.json()["createdAt"].endswith("Z")
    search_id = created.json()["id"]
    queued = await client.get(f"/job-searches/{search_id}")
    assert queued.json()["results"] == []
    assert queued.json()["parsedQuery"] is None

    with create_session_factory(engine)() as database:
        search = database.get(JobSearch, search_id)
        assert search is not None
        search.status = "completed"
        search.parsed_query = {"target_roles": ["backend developer"]}
        search.specialist_specs = [{"spec_id": "specialist-1"}]
        search.stats = {"serp_calls": 1}
        database.add(
            JobSearchResult(
                search_id=search.id,
                rank=1,
                title="Backend Developer",
                company="Acme",
                location="Remote",
                source_url="https://example.com/job",
                source_site="example.com",
                fit_score=90,
                fit_reason="Strong match",
                qualifications=["3 years"],
                tech_stack=["Python"],
                focus_findings={"tech_stack": ["Python"]},
                salary={"raw": "Rp 15 juta"},
                specialist_id="specialist-1",
                enrichment_status="not_needed",
            )
        )
        database.commit()

    completed = await client.get(f"/job-searches/{search_id}")
    body = completed.json()
    assert completed.status_code == 200
    assert body["status"] == "completed"
    assert body["parsedQuery"]["targetRoles"] == ["backend developer"]
    assert body["results"][0] == {
        "rank": 1,
        "title": "Backend Developer",
        "company": "Acme",
        "location": "Remote",
        "sourceUrl": "https://example.com/job",
        "sourceSite": "example.com",
        "postedAt": None,
        "fitScore": 90,
        "fitReason": "Strong match",
        "qualifications": ["3 years"],
        "techStack": ["Python"],
        "focusFindings": {"tech_stack": ["Python"]},
        "salary": {"raw": "Rp 15 juta", "min": None, "max": None, "currency": None, "period": None},
        "enrichment": "not_needed",
    }
    listed = await client.get("/job-searches")
    assert listed.status_code == 200
    assert listed.json()["searches"][0]["id"] == search_id


async def test_prompt_validation_owner_isolation_and_active_limit(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    allow_enqueue(monkeypatch)
    await register(client, "first@example.com")
    invalid = await client.post("/job-searches", json={"prompt": " short "})
    assert invalid.status_code == 400

    ids = []
    for index in range(3):
        response = await client.post(
            "/job-searches",
            json={"prompt": f"backend developer search {index}"},
        )
        assert response.status_code == 202
        ids.append(response.json()["id"])
    limited = await client.post(
        "/job-searches",
        json={"prompt": "another backend developer search"},
    )
    assert limited.status_code == 429
    assert limited.json() == {"error": "too_many_active_searches"}

    await client.post("/api/auth/sign-out")
    await register(client, "second@example.com")
    isolated = await client.get(f"/job-searches/{ids[0]}")
    assert isolated.status_code == 404


async def test_enqueue_failure_marks_search_failed(
    client: AsyncClient,
    engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_enqueue(_queue: object, _search_id: str) -> None:
        raise ConnectionError("Redis unavailable")

    monkeypatch.setattr(service, "enqueue_job_search", fail_enqueue)
    user = await register(client, "queue-failure@example.com")

    response = await client.post(
        "/job-searches",
        json={"prompt": "backend developer Python"},
    )

    assert response.status_code == 503
    with create_session_factory(engine)() as database:
        search = database.scalar(select(JobSearch).where(JobSearch.user_id == user["id"]))
        assert search is not None
        assert search.status == "failed"
        assert search.error_code == "queue_unavailable"
