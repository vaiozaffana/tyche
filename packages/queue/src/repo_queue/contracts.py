"""Stable JSON contracts for background jobs."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

JOB_SEARCH_TASK_NAME = "job_search.run"


class QueueModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class JobSearchPayload(QueueModel):
    search_id: UUID


class JobSearchTaskResult(QueueModel):
    search_id: UUID
    status: Literal["completed", "failed", "skipped"]
