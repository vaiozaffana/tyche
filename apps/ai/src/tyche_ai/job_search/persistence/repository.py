"""Job-search persistence using a caller-owned SQLAlchemy session."""

from repo_db import JobSearch, JobSearchResult, utc_now
from sqlalchemy import delete, func
from sqlalchemy.orm import Session
from sqlmodel import col, select

from tyche_ai.job_search.models import PipelineResult, RankedJob


class JobSearchRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, user_id: str, prompt: str) -> JobSearch:
        search = JobSearch(user_id=user_id, prompt=prompt)
        self.session.add(search)
        self.session.commit()
        self.session.refresh(search)
        return search

    def get(self, search_id: str) -> JobSearch | None:
        return self.session.get(JobSearch, search_id)

    def get_owned(self, search_id: str, user_id: str) -> JobSearch | None:
        return self.session.scalar(
            select(JobSearch).where(
                col(JobSearch.id) == search_id,
                col(JobSearch.user_id) == user_id,
            )
        )

    def list_recent(self, user_id: str, *, limit: int = 20) -> list[JobSearch]:
        return list(
            self.session.scalars(
                select(JobSearch)
                .where(col(JobSearch.user_id) == user_id)
                .order_by(col(JobSearch.created_at).desc())
                .limit(limit)
            )
        )

    def count_active(self, user_id: str) -> int:
        return (
            self.session.scalar(
                select(func.count())
                .select_from(JobSearch)
                .where(
                    col(JobSearch.user_id) == user_id,
                    col(JobSearch.status).in_(("queued", "running")),
                )
            )
            or 0
        )

    def list_results(self, search_id: str) -> list[JobSearchResult]:
        return list(
            self.session.scalars(
                select(JobSearchResult)
                .where(col(JobSearchResult.search_id) == search_id)
                .order_by(col(JobSearchResult.rank))
            )
        )

    def mark_running(self, search: JobSearch) -> None:
        search.status = "running"
        search.started_at = utc_now()
        search.completed_at = None
        search.error_code = None
        search.error_message = None
        self.session.commit()

    def mark_failed(self, search: JobSearch, *, code: str, message: str) -> None:
        search.status = "failed"
        search.error_code = code
        search.error_message = message[:500]
        search.completed_at = utc_now()
        self.session.commit()

    def complete(self, search: JobSearch, result: PipelineResult) -> None:
        try:
            self.session.execute(
                delete(JobSearchResult).where(col(JobSearchResult.search_id) == search.id)
            )
            self.session.add_all([self._result_row(search.id, ranked) for ranked in result.results])
            search.status = "completed"
            search.parsed_query = (
                result.parsed_query.model_dump(mode="json") if result.parsed_query else None
            )
            search.specialist_specs = result.specs
            search.stats = result.stats.model_dump(mode="json")
            search.run_log = result.run_log[:200]
            search.error_code = None
            search.error_message = None
            search.completed_at = utc_now()
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    @staticmethod
    def _result_row(search_id: str, ranked: RankedJob) -> JobSearchResult:
        candidate = ranked.candidate
        assessment = ranked.assessment
        salary = assessment.salary.model_dump(mode="json") if assessment.salary else None
        if salary is None and candidate.salary_raw:
            salary = {"raw": candidate.salary_raw}
        return JobSearchResult(
            search_id=search_id,
            rank=ranked.rank,
            title=candidate.title,
            company=candidate.company,
            location=candidate.location,
            source_url=candidate.source_url,
            source_site=candidate.source_site,
            posted_at=candidate.posted_at,
            description_snippet=candidate.description[:500],
            qualifications=assessment.qualifications,
            tech_stack=assessment.tech_stack,
            focus_findings=assessment.focus_findings,
            salary=salary,
            fit_score=assessment.fit_score,
            fit_reason=assessment.fit_reason,
            specialist_id=ranked.specialist_id,
            enrichment_status=ranked.enrichment_status,
        )
