"""Tries Groq first, falls back to the local Ollama model if Groq is
unavailable (rate limited, network error, bad/revoked API key, etc.).
Same generate_json(system_prompt, user_prompt) -> dict interface as
GroqClient/OllamaClient, so LlmFieldExtractor doesn't need to know two
providers are involved.

Groq is primary for now (faster on this CPU-only machine — Ollama's cold
start alone can take ~100s per call). Ollama stays wired in as the
fallback so extraction keeps working even if Groq's key is revoked or the
service is down, and remains the only option once GROQ_API_KEY is retired
for good (brief's "no third-party API" preference for this step).
"""

from __future__ import annotations

from config.logging_config import get_logger
from src.freep_pipeline.extraction.groq_client import GroqClient, GroqUnavailableError
from src.freep_pipeline.extraction.ollama_client import OllamaClient, OllamaUnavailableError

logger = get_logger(__name__)


class FallbackLlmClient:
    """Primary/fallback pair with a uniform generate_json() interface.
    Raises OllamaUnavailableError only if BOTH providers fail — the single
    exception type LlmFieldExtractor already knows to treat as
    "nothing extracted", never a reason to fabricate field values."""

    def __init__(self, primary: GroqClient | None = None, fallback: OllamaClient | None = None) -> None:
        self._primary = primary
        self._fallback = fallback or OllamaClient()

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        primary = self._primary
        if primary is None:
            try:
                primary = GroqClient()
            except GroqUnavailableError as exc:
                logger.warning("Groq client could not be constructed, using Ollama only: %s", exc)
                return self._fallback.generate_json(system_prompt, user_prompt)

        try:
            return primary.generate_json(system_prompt, user_prompt)
        except GroqUnavailableError as exc:
            logger.warning("Groq extraction failed, falling back to Ollama: %s", exc)

        try:
            return self._fallback.generate_json(system_prompt, user_prompt)
        except OllamaUnavailableError as exc:
            raise OllamaUnavailableError(f"Both Groq and Ollama unavailable: {exc}") from exc
