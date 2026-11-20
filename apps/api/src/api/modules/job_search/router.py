"""Authenticated polling API for job searches."""

from typing import cast

from celery import Celery
from fastapi import APIRouter, HTTPException, Request, status
from repo_db import JobSearch, JobSearchResult

from api.dependencies import CurrentAuthDependency, DatabaseDependency
from api.modules.job_search.schemas import (
    JobSearchCreatedResponse,
    JobSearchCreateInput,
    JobSearchDetailResponse,
    JobSearchListResponse,
    JobSearchResultResponse,
    JobSearchSalaryResponse,
    JobSearchSummaryResponse,
    SearchStatus,
)
from api.modules.job_search.service import (
    QueueUnavailableError,
    TooManyActiveSearchesError,
    create_search,
    list_searches,
    load_search,
)
from api.schemas import to_camel
from api.settings import Settings

router = APIRouter(prefix="/job-searches", tags=["job-searches"])


def _status(value: str) -> SearchStatus:
    if value not in {"queued", "running", "completed", "failed"}:
        raise ValueError("Invalid stored job-search status")
    return cast(SearchStatus, value)


def _camel_json(value: object) -> object:
    if isinstance(value, dict):
        return {to_camel(str(key)): _camel_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_camel_json(item) for item in value]
    return value


def _result_response(row: JobSearchResult) -> JobSearchResultResponse:
    return JobSearchResultResponse(
        rank=row.rank,
        title=row.title,
        company=row.company,
        location=row.location,
        source_url=row.source_url,
        source_site=row.source_site,
        posted_at=row.posted_at,
        fit_score=row.fit_score,
        fit_reason=row.fit_reason,
        qualifications=row.qualifications,
        tech_stack=row.tech_stack,
        focus_findings=row.focus_findings,
        salary=JobSearchSalaryResponse.model_validate(row.salary) if row.salary else None,
        enrichment=row.enrichment_status,
    )


def _detail_response(search: JobSearch, rows: list[JobSearchResult]) -> JobSearchDetailResponse:
    return JobSearchDetailResponse(
        id=search.id,
        status=_status(search.status),
        prompt=search.prompt,
        parsed_query=cast(dict[str, object] | None, _camel_json(search.parsed_query)),
        specialists=cast(list[dict[str, object]], _camel_json(search.specialist_specs)),
        stats=cast(dict[str, object], _camel_json(search.stats)),
        error_message=search.error_message,
        results=[_result_response(row) for row in rows],
        created_at=search.created_at,
        completed_at=search.completed_at,
    )


@router.post("", response_model=JobSearchCreatedResponse, status_code=status.HTTP_202_ACCEPTED)
def create_job_search(
    body: JobSearchCreateInput,
    request: Request,
    auth: CurrentAuthDependency,
    database: DatabaseDependency,
) -> JobSearchCreatedResponse:
    settings = cast(Settings, request.app.state.settings)
    try:
        search = create_search(
            database,
            cast(Celery, request.app.state.queue_app),
            user_id=auth.user.id,
            prompt=body.prompt,
            max_active=settings.job_search_max_active_per_user,
        )
    except TooManyActiveSearchesError as error:
        raise HTTPException(status_code=429, detail="too_many_active_searches") from error
    except QueueUnavailableError as error:
        raise HTTPException(status_code=503, detail="Job-search queue is unavailable.") from error
    return JobSearchCreatedResponse(
        id=search.id,
        status=_status(search.status),
        created_at=search.created_at,
    )


@router.get("/{search_id}", response_model=JobSearchDetailResponse)
def get_job_search(
    search_id: str,
    auth: CurrentAuthDependency,
    database: DatabaseDependency,
) -> JobSearchDetailResponse:
    loaded = load_search(database, search_id=search_id, user_id=auth.user.id)
    if loaded is None:
        raise HTTPException(status_code=404, detail="Job search not found.")
    return _detail_response(*loaded)


@router.get("", response_model=JobSearchListResponse)
def get_job_searches(
    auth: CurrentAuthDependency,
    database: DatabaseDependency,
) -> JobSearchListResponse:
    return JobSearchListResponse(
        searches=[
            JobSearchSummaryResponse(
                id=search.id,
                status=_status(search.status),
                prompt=search.prompt,
                created_at=search.created_at,
                completed_at=search.completed_at,
            )
            for search in list_searches(database, user_id=auth.user.id)
        ]
    )
