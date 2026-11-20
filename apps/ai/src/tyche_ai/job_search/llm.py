"""Structured LLM boundary and Gemini implementation."""

from collections import defaultdict, deque
from collections.abc import Callable
from typing import Literal, Protocol, TypeVar, cast

from google import genai
from google.genai import types
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)
ThinkingLevel = Literal["low", "medium"]


class TransientLLMError(RuntimeError):
    """A provider failure worth retrying."""


class PermanentLLMError(RuntimeError):
    """A provider failure that retrying cannot repair."""


class StructuredLLM(Protocol):
    def invoke_structured(
        self,
        *,
        system: str,
        user: str,
        schema: type[T],
        thinking_level: ThinkingLevel,
        max_output_tokens: int,
    ) -> T: ...


class _Response(Protocol):
    text: str | None


class _Models(Protocol):
    def generate_content(
        self, *, model: str, contents: str, config: types.GenerateContentConfig
    ) -> _Response: ...


class _Client(Protocol):
    @property
    def models(self) -> _Models: ...


def _provider_error(error: Exception) -> RuntimeError:
    status = cast(int | None, getattr(error, "code", getattr(error, "status_code", None)))
    message = f"Gemini request failed ({status or 'unknown status'})"
    if status in {408, 409, 429} or (status is not None and status >= 500):
        return TransientLLMError(message)
    return PermanentLLMError(message)


class GeminiStructuredLLM:
    def __init__(self, *, api_key: str, model: str, client: _Client | None = None) -> None:
        self.model = model
        self.client = client or cast(_Client, genai.Client(api_key=api_key))

    def invoke_structured(
        self,
        *,
        system: str,
        user: str,
        schema: type[T],
        thinking_level: ThinkingLevel,
        max_output_tokens: int,
    ) -> T:
        config = types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_output_tokens,
            response_mime_type="application/json",
            response_json_schema=schema.model_json_schema(),
            thinking_config=types.ThinkingConfig(
                thinking_level={
                    "low": types.ThinkingLevel.LOW,
                    "medium": types.ThinkingLevel.MEDIUM,
                }[thinking_level]
            ),
        )
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=user,
                config=config,
            )
        except Exception as error:
            raise _provider_error(error) from error
        if not response.text:
            raise PermanentLLMError("Gemini returned no structured response")
        return schema.model_validate_json(response.text)


ScriptedResponse = BaseModel | Exception | Callable[[], BaseModel]


class FakeStructuredLLM:
    def __init__(self) -> None:
        self._responses: dict[type[BaseModel], deque[ScriptedResponse]] = defaultdict(deque)
        self.calls: list[type[BaseModel]] = []

    def add(self, schema: type[T], *responses: T | Exception | Callable[[], T]) -> None:
        self._responses[schema].extend(responses)

    def invoke_structured(
        self,
        *,
        system: str,
        user: str,
        schema: type[T],
        thinking_level: ThinkingLevel,
        max_output_tokens: int,
    ) -> T:
        del system, user, thinking_level, max_output_tokens
        self.calls.append(schema)
        if not self._responses[schema]:
            raise AssertionError(f"No scripted response for {schema.__name__}")
        response = self._responses[schema].popleft()
        if isinstance(response, Exception):
            raise response
        result = response() if callable(response) else response
        return schema.model_validate(result)
