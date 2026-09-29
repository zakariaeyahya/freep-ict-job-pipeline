"""Primary LLM provider for field extraction. Same
generate_json(system_prompt, user_prompt) -> dict interface as
GroqClient/OllamaClient, so LlmFieldExtractor does not need to know which
provider it's talking to.

Sends job text to a third-party API — OPENAI_API_KEY must be treated as a
real secret (env var only, never committed).
"""

from __future__ import annotations

import json

from openai import OpenAI, OpenAIError

from config.logging_config import get_logger
from config.settings import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TIMEOUT_SECONDS

logger = get_logger(__name__)


class OpenAiUnavailableError(Exception):
    """Raised when the OpenAI API cannot be reached or errors out. Never a
    reason to fabricate field values — callers must treat this the same as
    "nothing extracted", per the never-fabricate-content rule."""


class OpenAiClient:
    """Thin wrapper around the official `openai` SDK's chat completions,
    with JSON mode enabled."""

    def __init__(
        self,
        api_key: str = OPENAI_API_KEY,
        model: str = OPENAI_MODEL,
        timeout_seconds: int = OPENAI_TIMEOUT_SECONDS,
    ) -> None:
        if not api_key:
            raise OpenAiUnavailableError("OPENAI_API_KEY is not set")
        # max_retries=0: fail immediately on a 429/5xx instead of waiting
        # out the SDK's built-in backoff, so the caller can fall back to
        # Groq right away instead of stalling the scan (same reasoning as
        # GroqClient's max_retries=0).
        self._client = OpenAI(api_key=api_key, timeout=timeout_seconds, max_retries=0)
        self._model = model

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        """Some OpenAI models (reasoning-family, e.g. gpt-6-astra) reject a
        non-default temperature outright, so temperature is omitted here
        rather than pinned to 0 — unlike GroqClient/OllamaClient, exact
        determinism across scans isn't guaranteed for every possible model
        configured via OPENAI_MODEL."""
        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
        except OpenAIError as exc:
            raise OpenAiUnavailableError(f"OpenAI request failed: {exc}") from exc

        content = completion.choices[0].message.content or ""
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise OpenAiUnavailableError(f"OpenAI returned non-JSON content: {content[:200]}") from exc
