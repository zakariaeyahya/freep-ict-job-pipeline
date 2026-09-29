"""Tries OpenAI first, falls back to Groq if OpenAI is unavailable (rate
limited, network error, bad/revoked API key, etc.). Same
generate_json(system_prompt, user_prompt) -> dict interface as
OpenAiClient/GroqClient, so LlmFieldExtractor doesn't need to know two
providers are involved.

No local (Ollama) fallback: on a CPU-only host without a GPU, a 7B model's
response time is highly variable and can dominate the scan's wall-clock
time (observed several minutes per call), so extraction here is
Groq-or-nothing once OpenAI fails — a scan never blocks on a slow local
model (brief's "never blocks a scan" rule for best-effort extraction).
"""

from __future__ import annotations

from config.logging_config import get_logger
from src.freep_pipeline.extraction.groq_client import GroqClient, GroqUnavailableError
from src.freep_pipeline.extraction.openai_client import OpenAiClient, OpenAiUnavailableError

logger = get_logger(__name__)


class FallbackLlmClient:
    """Primary/fallback pair with a uniform generate_json() interface.
    Raises GroqUnavailableError only if BOTH providers fail — the single
    exception type LlmFieldExtractor already knows to treat as
    "nothing extracted", never a reason to fabricate field values."""

    def __init__(self, primary: OpenAiClient | None = None, fallback: GroqClient | None = None) -> None:
        self._primary = primary
        self._fallback = fallback

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        primary = self._primary
        if primary is None:
            try:
                primary = OpenAiClient()
            except OpenAiUnavailableError as exc:
                logger.warning("OpenAI client could not be constructed, trying Groq only: %s", exc)
                return self._call_fallback(system_prompt, user_prompt)

        try:
            return primary.generate_json(system_prompt, user_prompt)
        except OpenAiUnavailableError as exc:
            logger.warning("OpenAI extraction failed, falling back to Groq: %s", exc)

        return self._call_fallback(system_prompt, user_prompt)

    def _call_fallback(self, system_prompt: str, user_prompt: str) -> dict:
        fallback = self._fallback
        if fallback is None:
            try:
                fallback = GroqClient()
            except GroqUnavailableError as exc:
                raise GroqUnavailableError(f"Both OpenAI and Groq unavailable: {exc}") from exc

        try:
            return fallback.generate_json(system_prompt, user_prompt)
        except GroqUnavailableError as exc:
            raise GroqUnavailableError(f"Both OpenAI and Groq unavailable: {exc}") from exc
