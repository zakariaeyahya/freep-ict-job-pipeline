"""Temporary stand-in for OllamaClient, used only while the local Ollama
model is still being pulled (docker exec ... ollama pull). Same
generate_json(system_prompt, user_prompt) -> dict interface, so
LlmFieldExtractor does not need to know which provider it's talking to.

Unlike Ollama this sends job text to a third-party API — GROQ_API_KEY must
be treated as a real secret (env var only, never committed) and this
client should be swapped back to OllamaClient once a model is pulled
locally (brief's "no third-party API" preference for this extraction
step).
"""

from __future__ import annotations

import json

from groq import Groq, GroqError

from config.logging_config import get_logger
from config.settings import GROQ_API_KEY, GROQ_MODEL, GROQ_TIMEOUT_SECONDS

logger = get_logger(__name__)


class GroqUnavailableError(Exception):
    """Raised when the Groq API cannot be reached or errors out. Never a
    reason to fabricate field values — callers must treat this the same as
    "nothing extracted", per the never-fabricate-content rule."""


class GroqClient:
    """Thin wrapper around the official `groq` SDK's chat completions, with
    JSON mode enabled."""

    def __init__(
        self,
        api_key: str = GROQ_API_KEY,
        model: str = GROQ_MODEL,
        timeout_seconds: int = GROQ_TIMEOUT_SECONDS,
    ) -> None:
        if not api_key:
            raise GroqUnavailableError("GROQ_API_KEY is not set")
        self._client = Groq(api_key=api_key, timeout=timeout_seconds)
        self._model = model

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        """Deterministic (temperature=0) so the same source text yields the
        same result across scans, per the pipeline's reproducibility
        requirement."""
        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
        except GroqError as exc:
            raise GroqUnavailableError(f"Groq request failed: {exc}") from exc

        content = completion.choices[0].message.content or ""
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise GroqUnavailableError(f"Groq returned non-JSON content: {content[:200]}") from exc
