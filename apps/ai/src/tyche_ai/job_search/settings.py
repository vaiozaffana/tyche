"""Environment-owned configuration for the job-search pipeline."""

from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class JobSearchSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    serpapi_api_key: str = ""
    firecrawl_api_key: str = ""
    gemini_api_key: str = ""
    llm_model: str = "gemini-3.8-flash"
    job_search_fake_mode: bool = False
    job_search_thinking_level: Literal["low", "medium"] = "low"
    job_search_max_serp_calls: int = Field(default=2, ge=1, le=5)
    job_search_max_firecrawl_calls: int = Field(default=5, ge=0, le=20)
    job_search_max_llm_jobs: int = Field(default=10, ge=1, le=50)
    job_search_max_specialists: int = Field(default=3, ge=1, le=3)
    job_search_max_results: int = Field(default=10, ge=1, le=50)
    job_search_max_concurrency: int = Field(default=4, ge=1, le=16)
    job_search_min_description_chars: int = Field(default=500, ge=100, le=5_000)
    job_search_title_match_threshold: float = Field(default=0.5, ge=0, le=1)
    job_search_scrape_blocked_domains: Annotated[tuple[str, ...], NoDecode] = ("linkedin.com",)
    job_search_scrape_cache_ttl_hours: int = Field(default=24, ge=1, le=720)

    @field_validator("job_search_scrape_blocked_domains", mode="before")
    @classmethod
    def parse_domains(cls, value: object) -> object:
        if isinstance(value, str):
            return tuple(item.strip() for item in value.split(",") if item.strip())
        return value
