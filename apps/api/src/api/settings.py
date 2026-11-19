from typing import Annotated, Literal
from urllib.parse import urlparse

from pydantic import BeforeValidator, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


def split_origins(value: object) -> object:
    if isinstance(value, str):
        return [item.strip() for item in value.split(",")]
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    node_env: Literal["development", "test", "production"] = Field(
        default="development", alias="NODE_ENV"
    )
    api_port: int = Field(default=8000, ge=1, le=65535, alias="API_PORT")
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:15432/tyche",
        alias="DATABASE_URL",
    )
    client_origins: Annotated[list[str], NoDecode, BeforeValidator(split_origins)] = Field(
        default_factory=lambda: ["http://localhost:3000"], alias="CLIENT_ORIGINS"
    )
    session_cookie_secure: bool | None = Field(default=None, alias="SESSION_COOKIE_SECURE")

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if urlparse(value).scheme not in {"postgresql", "postgresql+psycopg", "sqlite"}:
            raise ValueError("DATABASE_URL must use PostgreSQL or SQLite.")
        return value

    @model_validator(mode="after")
    def validate_origins(self) -> "Settings":
        if not self.client_origins:
            raise ValueError("CLIENT_ORIGINS must contain at least one origin.")
        for origin in self.client_origins:
            parsed = urlparse(origin)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.netloc
                or parsed.path not in {"", "/"}
                or parsed.params
                or parsed.query
                or parsed.fragment
                or origin.endswith("/")
            ):
                raise ValueError("CLIENT_ORIGINS entries must be http(s) origins without paths.")
        return self

    @property
    def secure_cookies(self) -> bool:
        if self.session_cookie_secure is not None:
            return self.session_cookie_secure
        return self.node_env == "production"
