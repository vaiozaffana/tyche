from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    redis_url: str = Field(default="redis://localhost:16379/0", alias="REDIS_URL")
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:15432/tyche",
        alias="DATABASE_URL",
    )

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, value: str) -> str:
        if urlparse(value).scheme not in {"redis", "rediss"}:
            raise ValueError("REDIS_URL must use redis or rediss.")
        return value

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if urlparse(value).scheme not in {"postgresql", "postgresql+psycopg", "sqlite"}:
            raise ValueError("DATABASE_URL must use PostgreSQL or SQLite.")
        return value
