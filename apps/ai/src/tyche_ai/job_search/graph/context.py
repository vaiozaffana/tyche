"""Per-run dependencies passed through LangGraph runtime context."""

from dataclasses import dataclass

from tyche_ai.job_search.llm import StructuredLLM
from tyche_ai.job_search.models import Budget
from tyche_ai.job_search.settings import JobSearchSettings
from tyche_ai.job_search.tools.cache import ScrapeCache
from tyche_ai.job_search.tools.firecrawl import PageReader
from tyche_ai.job_search.tools.serp import JobSearchProvider


@dataclass(frozen=True, slots=True)
class RunContext:
    search_id: str
    llm: StructuredLLM
    provider: JobSearchProvider
    reader: PageReader
    cache: ScrapeCache
    settings: JobSearchSettings
    budget: Budget
