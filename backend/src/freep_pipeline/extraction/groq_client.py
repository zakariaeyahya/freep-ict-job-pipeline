"""Fallback LLM provider for field extraction, used when OpenAI is
unavailable. Same generate_json(system_prompt, user_prompt) -> dict
interface as OpenAiClient, so LlmFieldExtractor does not need to know
which provider it's talking to.

Sends job text to a third-party API — GROQ_API_KEY must be treated as a
real secret (env var only, never committed).
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
        # max_retries=0: the SDK's default retry behavior waits out a
        # 429's Retry-After (observed 7-20s per attempt against this
        # account's rate limit) before ever raising — which defeats the
        # whole point of FallbackLlmClient's fast fallback to Ollama.
        # Failing immediately on the first 429 lets the caller fall back
        # right away instead of stalling the scan for tens of seconds per
        # job.
        self._client = Groq(api_key=api_key, timeout=timeout_seconds, max_retries=0)
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
