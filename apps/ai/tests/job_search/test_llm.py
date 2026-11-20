import json
from typing import Any

import pytest
from google.genai import types
from pydantic import BaseModel

from tyche_ai.job_search.llm import (
    FakeStructuredLLM,
    GeminiStructuredLLM,
    PermanentLLMError,
    TransientLLMError,
)


class Answer(BaseModel):
    value: str


class FakeModels:
    def __init__(
        self, *, text: str | None = '{"value":"ok"}', error: Exception | None = None
    ) -> None:
        self.text = text
        self.error = error
        self.config: types.GenerateContentConfig | None = None

    def generate_content(
        self,
        *,
        model: str,
        contents: str,
        config: types.GenerateContentConfig,
    ) -> Any:
        assert model == "gemini-3.8-flash"
        assert contents == "user"
        self.config = config
        if self.error:
            raise self.error
        return type("Response", (), {"text": self.text})()


class FakeClient:
    def __init__(self, models: FakeModels) -> None:
        self.models = models


class ProviderFailure(Exception):
    def __init__(self, code: int) -> None:
        self.code = code


def invoke(models: FakeModels) -> Answer:
    return GeminiStructuredLLM(
        api_key="not-a-real-key",
        model="gemini-3.8-flash",
        client=FakeClient(models),
    ).invoke_structured(
        system="system",
        user="user",
        schema=Answer,
        thinking_level="low",
        max_output_tokens=100,
    )


def test_gemini_uses_only_supported_structured_output_settings() -> None:
    models = FakeModels()

    assert invoke(models) == Answer(value="ok")

    assert models.config is not None
    payload = models.config.model_dump(by_alias=True, exclude_none=True)
    assert payload["thinkingConfig"] == {"thinkingLevel": "LOW"}
    assert payload["responseMimeType"] == "application/json"
    assert json.loads(json.dumps(payload["responseJsonSchema"]))["title"] == "Answer"
    assert {"candidateCount", "temperature", "topP", "topK"}.isdisjoint(payload)


@pytest.mark.parametrize("code", [408, 409, 429, 500, 503])
def test_gemini_classifies_retryable_provider_errors(code: int) -> None:
    with pytest.raises(TransientLLMError):
        invoke(FakeModels(error=ProviderFailure(code)))


def test_gemini_classifies_permanent_provider_errors() -> None:
    with pytest.raises(PermanentLLMError):
        invoke(FakeModels(error=ProviderFailure(400)))


def test_fake_llm_returns_scripted_models() -> None:
    fake = FakeStructuredLLM()
    fake.add(Answer, Answer(value="first"), Answer(value="second"))

    first = fake.invoke_structured(
        system="ignored",
        user="ignored",
        schema=Answer,
        thinking_level="low",
        max_output_tokens=50,
    )

    assert first.value == "first"
    assert fake.calls == [Answer]
