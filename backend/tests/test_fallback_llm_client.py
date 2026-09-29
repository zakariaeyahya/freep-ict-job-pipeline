"""FallbackLlmClient: OpenAI primary, Groq fallback. Verifies the actual
fallback behavior — Groq is only ever called when OpenAI fails — using
fake clients so no real network call happens in this suite.
"""

from __future__ import annotations

import pytest

from src.freep_pipeline.extraction.fallback_llm_client import FallbackLlmClient
from src.freep_pipeline.extraction.groq_client import GroqUnavailableError
from src.freep_pipeline.extraction.openai_client import OpenAiUnavailableError


class _FakeClient:
    def __init__(self, response: dict | None = None, raises: Exception | None = None) -> None:
        self._response = response
        self._raises = raises
        self.calls = 0

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        self.calls += 1
        if self._raises:
            raise self._raises
        return self._response


def test_uses_openai_result_without_touching_groq_when_openai_succeeds() -> None:
    openai = _FakeClient(response={"skills": ["Python"]})
    groq = _FakeClient(response={"skills": ["should never be returned"]})
    client = FallbackLlmClient(primary=openai, fallback=groq)

    result = client.generate_json("system", "user")

    assert result == {"skills": ["Python"]}
    assert openai.calls == 1
    assert groq.calls == 0


def test_falls_back_to_groq_when_openai_raises() -> None:
    openai = _FakeClient(raises=OpenAiUnavailableError("rate limited"))
    groq = _FakeClient(response={"skills": ["from groq"]})
    client = FallbackLlmClient(primary=openai, fallback=groq)

    result = client.generate_json("system", "user")

    assert result == {"skills": ["from groq"]}
    assert openai.calls == 1
    assert groq.calls == 1


def test_raises_when_both_providers_fail() -> None:
    openai = _FakeClient(raises=OpenAiUnavailableError("rate limited"))
    groq = _FakeClient(raises=GroqUnavailableError("connection refused"))
    client = FallbackLlmClient(primary=openai, fallback=groq)

    with pytest.raises(GroqUnavailableError):
        client.generate_json("system", "user")

    assert openai.calls == 1
    assert groq.calls == 1


def test_missing_openai_api_key_skips_straight_to_groq(monkeypatch) -> None:
    """FallbackLlmClient(primary=None) tries to construct a real
    OpenAiClient lazily — if that fails (e.g. no OPENAI_API_KEY
    configured), it must fall back to Groq rather than propagating the
    construction error. Forces the "no key" path regardless of this
    environment's actual .env, so the test doesn't depend on whether
    OPENAI_API_KEY happens to be set."""
    from src.freep_pipeline.extraction import fallback_llm_client

    def _raise_no_key(*args, **kwargs):
        raise OpenAiUnavailableError("OPENAI_API_KEY is not set")

    monkeypatch.setattr(fallback_llm_client, "OpenAiClient", _raise_no_key)
    groq = _FakeClient(response={"skills": ["from groq"]})
    client = FallbackLlmClient(primary=None, fallback=groq)

    result = client.generate_json("system", "user")

    assert result == {"skills": ["from groq"]}
    assert groq.calls == 1
