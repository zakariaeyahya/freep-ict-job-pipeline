"""LlmFieldExtractor's core guarantee: the never-fabricate-content rule
(CLAUDE.md) must hold even when the LLM itself misbehaves — every returned
value is checked to be an exact substring of the source text before being
trusted. Never make a real network call here: the LLM client is replaced
with a fake so these tests are fast and deterministic.
"""

from __future__ import annotations

import pytest

from src.freep_pipeline.extraction.groq_client import GroqUnavailableError
from src.freep_pipeline.extraction.llm_field_extractor import ExtractedFields, LlmFieldExtractor

_PROMPT_SPEC = {
    "system_prompt": "irrelevant for these tests — the fake client ignores it",
    "list_fields": ["education", "experience", "skills", "methods", "certifications", "languages"],
    "text_fields": ["contract_type", "screening"],
    "bool_fields": ["zzp_allowed", "vog"],
    "int_fields": ["positions", "max_candidates"],
}


class _FakeLlmClient:
    def __init__(self, response: dict | None = None, raises: Exception | None = None) -> None:
        self._response = response or {}
        self._raises = raises
        self.last_call = None

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        self.last_call = (system_prompt, user_prompt)
        if self._raises:
            raise self._raises
        return self._response


def _extractor(response: dict | None = None, raises: Exception | None = None) -> LlmFieldExtractor:
    client = _FakeLlmClient(response=response, raises=raises)
    return LlmFieldExtractor(client=client, prompt_spec=_PROMPT_SPEC)


def test_values_that_are_exact_substrings_of_the_source_are_kept() -> None:
    hard_requirements = ["Kandidaat is geen ZZP'er en werkt in loondienst", "HBO werk- en denkniveau"]
    response = {
        "education": ["HBO werk- en denkniveau"],
        "zzp_allowed": False,
        "contract_type": "detachering",
    }
    extractor = _extractor(response=response)

    result = extractor.extract(title="detachering", hard_requirements=hard_requirements, wishes=[])

    assert result.education == ["HBO werk- en denkniveau"]
    assert result.zzp_allowed is False
    assert result.contract_type == "detachering"


def test_a_paraphrased_value_not_present_verbatim_in_the_source_is_discarded() -> None:
    """The core anti-fabrication guarantee: if the model invents or
    paraphrases text that does not appear in the source, it must never
    reach the published record."""
    hard_requirements = ["Kandidaat heeft een afgeronde HBO opleiding richting Informatica"]
    response = {"education": ["Master's degree in Computer Science"]}  # not in the source at all
    extractor = _extractor(response=response)

    result = extractor.extract(title="Developer", hard_requirements=hard_requirements, wishes=[])

    assert result.education == []


def test_mixed_batch_keeps_only_the_grounded_items() -> None:
    hard_requirements = ["Ervaring met Python", "Kennis van SQL"]
    response = {"skills": ["Ervaring met Python", "Fabricated skill not in source"]}
    extractor = _extractor(response=response)

    result = extractor.extract(title="Dev", hard_requirements=hard_requirements, wishes=[])

    assert result.skills == ["Ervaring met Python"]


def test_wrong_types_from_the_model_are_ignored_not_coerced() -> None:
    """A boolean field returned as a string, or a list field returned as a
    plain string, must be treated as 'nothing extracted' rather than
    silently coerced into something that looks valid."""
    response = {
        "zzp_allowed": "false",  # string, not a real bool -> must be ignored
        "positions": "2",  # string, not a real int -> must be ignored
        "skills": "Python",  # not a list -> must be ignored
    }
    extractor = _extractor(response=response)

    result = extractor.extract(title="Dev", hard_requirements=["Python ervaring"], wishes=[])

    assert result.zzp_allowed is None
    assert result.positions is None
    assert result.skills == []


def test_unavailable_llm_returns_empty_fields_instead_of_raising() -> None:
    """Extraction is best-effort enrichment, not a required pipeline step
    — a down/misconfigured LLM must never block scanning or publishing."""
    extractor = _extractor(raises=GroqUnavailableError("connection refused"))

    result = extractor.extract(title="Dev", hard_requirements=["Python ervaring"], wishes=[])

    assert result == ExtractedFields()


def test_empty_source_text_skips_the_llm_call_entirely() -> None:
    client = _FakeLlmClient(response={"skills": ["should never be seen"]})
    extractor = LlmFieldExtractor(client=client, prompt_spec=_PROMPT_SPEC)

    result = extractor.extract(title="", hard_requirements=[], wishes=[])

    assert result == ExtractedFields()
    assert client.last_call is None


@pytest.mark.parametrize(
    "field_name,bad_value",
    [("zzp_allowed", None), ("vog", "unknown"), ("positions", None), ("max_candidates", "many")],
)
def test_missing_or_invalid_scalar_fields_default_to_none(field_name: str, bad_value) -> None:
    response = {field_name: bad_value} if bad_value is not None else {}
    extractor = _extractor(response=response)

    result = extractor.extract(title="Dev", hard_requirements=["Some requirement"], wishes=[])

    assert getattr(result, field_name) is None
