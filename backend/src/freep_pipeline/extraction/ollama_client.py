"""Thin HTTP client for a local Ollama server (brief §4.2's profile/
engagement/procedure extraction — see llm_field_extractor.py).

Runs entirely on the operator's own machine: no job text is ever sent to a
third-party API, and there is no API key to manage or leak.
"""

from __future__ import annotations

import json

import requests

from config.logging_config import get_logger
from config.settings import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT_SECONDS

logger = get_logger(__name__)


class OllamaUnavailableError(Exception):
    """Raised when the local Ollama server cannot be reached or errors out.
    Never a reason to fabricate field values — callers must treat this the
    same as "nothing extracted", per the never-fabricate-content rule."""


class OllamaClient:
    """Calls Ollama's /api/chat with JSON-mode output enabled.

    No request timeout by default (timeout_seconds=None): on a CPU-only
    Ollama host, model load + inference time is highly variable (observed
    ~100s cold start for a single short prompt on this machine) and an
    arbitrary cutoff would reject valid-but-slow responses rather than
    actual failures. A deliberate deviation from the project's usual
    "always set an outbound timeout" rule, made for this specific
    hardware-bound case — not a default to copy elsewhere."""

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_MODEL,
        timeout_seconds: int | None = OLLAMA_TIMEOUT_SECONDS,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout_seconds = timeout_seconds

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        """Sends a chat request constrained to JSON output (Ollama's
        `format: "json"`) and returns the parsed object. Deterministic
        (temperature=0) so the same source text yields the same result
        across scans, per the pipeline's reproducibility requirement."""
        try:
            response = requests.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "format": "json",
                    "stream": False,
                    "options": {"temperature": 0},
                },
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise OllamaUnavailableError(f"Ollama request failed: {exc}") from exc

        content = response.json().get("message", {}).get("content", "")
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise OllamaUnavailableError(f"Ollama returned non-JSON content: {content[:200]}") from exc
