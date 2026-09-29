"""FallbackLlmClient: Groq primary, Ollama fallback. Verifies the actual
fallback behavior — Ollama is only ever called when Groq fails — using
fake clients so no real network call happens in this suite.
"""

from __future__ import annotations

import pytest

from src.freep_pipeline.extraction.fallback_llm_client import FallbackLlmClient
from src.freep_pipeline.extraction.groq_client import GroqUnavailableError
from src.freep_pipeline.extraction.ollama_client import OllamaUnavailableError


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


def test_uses_groq_result_without_touching_ollama_when_groq_succeeds() -> None:
    groq = _FakeClient(response={"skills": ["Python"]})
    ollama = _FakeClient(response={"skills": ["should never be returned"]})
    client = FallbackLlmClient(primary=groq, fallback=ollama)

    result = client.generate_json("system", "user")

    assert result == {"skills": ["Python"]}
    assert groq.calls == 1
    assert ollama.calls == 0


def test_falls_back_to_ollama_when_groq_raises() -> None:
    groq = _FakeClient(raises=GroqUnavailableError("rate limited"))
    ollama = _FakeClient(response={"skills": ["from ollama"]})
    client = FallbackLlmClient(primary=groq, fallback=ollama)

    result = client.generate_json("system", "user")

    assert result == {"skills": ["from ollama"]}
    assert groq.calls == 1
    assert ollama.calls == 1


def test_raises_when_both_providers_fail() -> None:
    groq = _FakeClient(raises=GroqUnavailableError("rate limited"))
    ollama = _FakeClient(raises=OllamaUnavailableError("connection refused"))
    client = FallbackLlmClient(primary=groq, fallback=ollama)

    with pytest.raises(OllamaUnavailableError):
        client.generate_json("system", "user")

    assert groq.calls == 1
    assert ollama.calls == 1


def test_missing_groq_api_key_skips_straight_to_ollama(monkeypatch) -> None:
    """FallbackLlmClient(primary=None) tries to construct a real GroqClient
    lazily — if that fails (e.g. no GROQ_API_KEY configured), it must fall
    back to Ollama rather than propagating the construction error. Forces
    the "no key" path regardless of this environment's actual .env, so the
    test doesn't depend on whether GROQ_API_KEY happens to be set."""
    from src.freep_pipeline.extraction import fallback_llm_client

    def _raise_no_key(*args, **kwargs):
        raise GroqUnavailableError("GROQ_API_KEY is not set")

    monkeypatch.setattr(fallback_llm_client, "GroqClient", _raise_no_key)
    ollama = _FakeClient(response={"skills": ["from ollama"]})
    client = FallbackLlmClient(primary=None, fallback=ollama)

    result = client.generate_json("system", "user")

    assert result == {"skills": ["from ollama"]}
    assert ollama.calls == 1
