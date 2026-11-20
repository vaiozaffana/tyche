"""SQLModel tables for asynchronous job-search runs."""

from datetime import datetime
from typing import Any, ClassVar
from uuid import uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Text,
    UniqueConstraint,
    desc,
)
from sqlmodel import Field, SQLModel

from repo_db.models import Base, utc_now


def new_id() -> str:
    return str(uuid4())


class JobSearch(SQLModel, table=True):
    __tablename__ = "job_searches"
    metadata: ClassVar = Base.metadata
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'running', 'completed', 'failed')",
            name="ck_job_searches_status",
        ),
        Index("ix_job_searches_user_created", "user_id", desc("created_at")),
    )

    id: str = Field(default_factory=new_id, primary_key=True, sa_type=Text)
    user_id: str = Field(
        sa_column=Column(Text, ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    )
    prompt: str = Field(sa_column=Column(Text, nullable=False))
    status: str = Field(default="queued", sa_column=Column(Text, nullable=False, default="queued"))
    parsed_query: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    specialist_specs: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False, default=list),
    )
    stats: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON, nullable=False, default=dict)
    )
    run_log: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False, default=list),
    )
    error_code: str | None = Field(default=None, sa_column=Column(Text))
    error_message: str | None = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime, nullable=False, default=utc_now),
    )
    started_at: datetime | None = Field(default=None, sa_column=Column(DateTime))
    completed_at: datetime | None = Field(default=None, sa_column=Column(DateTime))


class JobSearchResult(SQLModel, table=True):
    __tablename__ = "job_search_results"
    metadata: ClassVar = Base.metadata
    __table_args__ = (
        CheckConstraint(
            "fit_score IS NULL OR fit_score BETWEEN 0 AND 100", name="ck_job_results_score"
        ),
        CheckConstraint(
            "enrichment_status IN ('not_needed', 'scraped', 'cached', 'skipped', 'failed')",
            name="ck_job_results_enrichment",
        ),
        UniqueConstraint("search_id", "rank", name="uq_job_results_search_rank"),
        Index("ix_job_search_results_search", "search_id"),
    )

    id: str = Field(default_factory=new_id, primary_key=True, sa_type=Text)
    search_id: str = Field(
        sa_column=Column(Text, ForeignKey("job_searches.id", ondelete="CASCADE"), nullable=False)
    )
    rank: int = Field(gt=0)
    title: str = Field(sa_column=Column(Text, nullable=False))
    company: str = Field(sa_column=Column(Text, nullable=False))
    location: str = Field(sa_column=Column(Text, nullable=False))
    source_url: str | None = Field(default=None, sa_column=Column(Text))
    source_site: str | None = Field(default=None, sa_column=Column(Text))
    posted_at: str | None = Field(default=None, sa_column=Column(Text))
    description_snippet: str = Field(default="", sa_column=Column(Text, nullable=False, default=""))
    qualifications: list[str] = Field(
        default_factory=list, sa_column=Column(JSON, nullable=False, default=list)
    )
    tech_stack: list[str] = Field(
        default_factory=list, sa_column=Column(JSON, nullable=False, default=list)
    )
    focus_findings: dict[str, list[str]] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False, default=dict),
    )
    salary: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    fit_score: int | None = Field(default=None)
    fit_reason: str | None = Field(default=None, sa_column=Column(Text))
    specialist_id: str = Field(sa_column=Column(Text, nullable=False))
    enrichment_status: str = Field(sa_column=Column(Text, nullable=False))


class ScrapeCacheEntry(SQLModel, table=True):
    __tablename__ = "scrape_cache"
    metadata: ClassVar = Base.metadata
    __table_args__ = (
        CheckConstraint("status IN ('ok', 'failed', 'blocked')", name="ck_scrape_cache_status"),
        Index("ix_scrape_cache_fetched_at", "fetched_at"),
    )

    url_hash: str = Field(primary_key=True, sa_type=Text)
    url: str = Field(sa_column=Column(Text, nullable=False))
    status: str = Field(sa_column=Column(Text, nullable=False))
    content: str = Field(default="", sa_column=Column(Text, nullable=False, default=""))
    fetched_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime, nullable=False, default=utc_now),
    )
