import pytest
from pydantic import ValidationError

from api.settings import Settings


def test_settings_split_client_origins() -> None:
    settings = Settings.model_validate(
        {"CLIENT_ORIGINS": "https://app.example.com, http://localhost:3000"}
    )
    assert settings.client_origins == ["https://app.example.com", "http://localhost:3000"]


def test_production_uses_secure_cookies_unless_explicitly_overridden() -> None:
    assert Settings(NODE_ENV="production").secure_cookies is True
    assert Settings(NODE_ENV="production", SESSION_COOKIE_SECURE=False).secure_cookies is False


@pytest.mark.parametrize(
    "origins", ["", "https://app.example.com/path", "https://app.example.com,"]
)
def test_settings_reject_invalid_origins(origins: str) -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"CLIENT_ORIGINS": origins})
