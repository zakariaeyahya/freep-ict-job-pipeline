"""Extracts profile/engagement/procedure signals (brief §4.2) from a job's
free-text requirements/wishes/description via an LLM (OpenAI primary, Groq
fallback — see FallbackLlmClient).

Why an LLM here and not more regex/BeautifulSoup: Freep's detail pages do
not expose these as separate HTML fields — "Geen ZZP", "afgeronde HBO
opleiding", "detachering" all appear as prose mixed into the eisen/wensen
lists, in inconsistent phrasing across offers (verified against a real
sample, ../../offre.md). A fixed set of regexes would be brittle; a
constrained LLM classification handles the phrasing variance.

The never-fabricate-content rule (CLAUDE.md) still applies to LLM output:
every text value the model returns is verified to be an EXACT substring of
the source text before being trusted. A value that doesn't match verbatim
is discarded (treated as not found), never silently kept as a paraphrase.
This is enforced here, not left to the model's good behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from config.logging_config import get_logger
from src.freep_pipeline.extraction.fallback_llm_client import FallbackLlmClient
from src.freep_pipeline.extraction.groq_client import GroqUnavailableError

logger = get_logger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "profile_engagement_procedure.yaml"


def _load_prompt_spec() -> dict[str, Any]:
    with open(_PROMPT_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


@dataclass
class ExtractedFields:
    education: list[str] = field(default_factory=list)
    experience: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    contract_type: str | None = None
    zzp_allowed: bool | None = None
    screening: str | None = None
    vog: bool | None = None
    positions: int | None = None
    max_candidates: int | None = None


class LlmFieldExtractor:
    """Wraps the LLM client (FallbackLlmClient by default: OpenAI primary,
    Groq fallback) with the prompt and the anti-fabrication verification
    pass. Never raises on a down/misbehaving LLM — extraction is a
    best-effort enrichment, not a required step; a job is stored and
    published with these groups empty rather than blocked (brief's
    never-fabricate rule takes priority over completeness)."""

    def __init__(self, client: Any | None = None, prompt_spec: dict[str, Any] | None = None) -> None:
        self._client = client or FallbackLlmClient()
        spec = prompt_spec or _load_prompt_spec()
        self._system_prompt: str = spec["system_prompt"]
        self._list_fields: tuple[str, ...] = tuple(spec["list_fields"])
        self._text_fields: tuple[str, ...] = tuple(spec["text_fields"])
        self._bool_fields: tuple[str, ...] = tuple(spec["bool_fields"])
        self._int_fields: tuple[str, ...] = tuple(spec["int_fields"])

    def extract(self, title: str, hard_requirements: list[str], wishes: list[str]) -> ExtractedFields:
        source_text = self._build_source_text(title, hard_requirements, wishes)
        if not source_text.strip():
            return ExtractedFields()

        try:
            raw = self._client.generate_json(self._system_prompt, source_text)
        except GroqUnavailableError as exc:
            # FallbackLlmClient only raises this after BOTH OpenAI and Groq
            # have failed — the client-agnostic "give up" signal here.
            logger.warning("LLM field extraction skipped (no provider available): %s", exc)
            return ExtractedFields()

        return self._verify_against_source(raw, source_text)

    @staticmethod
    def _build_source_text(title: str, hard_requirements: list[str], wishes: list[str]) -> str:
        lines = [title] if title else []
        lines += hard_requirements + wishes
        return "\n".join(lines)

    def _verify_against_source(self, raw: dict, source_text: str) -> ExtractedFields:
        """Every text value must be an exact substring of source_text — the
        only guard against the model paraphrasing or inventing content."""
        result = ExtractedFields()

        for field_name in self._list_fields:
            candidates = raw.get(field_name)
            if isinstance(candidates, list):
                verified = [item for item in candidates if isinstance(item, str) and item in source_text]
                setattr(result, field_name, verified)

        for field_name in self._text_fields:
            value = raw.get(field_name)
            if isinstance(value, str) and value in source_text:
                setattr(result, field_name, value)

        for field_name in self._bool_fields:
            value = raw.get(field_name)
            if isinstance(value, bool):
                setattr(result, field_name, value)

        for field_name in self._int_fields:
            value = raw.get(field_name)
            if isinstance(value, int) and not isinstance(value, bool):
                setattr(result, field_name, value)

        return result
