"""Verifies ScanPipeline skips the LLM call for a job whose HTML-parsed
content is unchanged since the last scan, reusing the previous
observation's LLM-derived fields instead — pure wasted time otherwise
(temperature=0 means re-extracting unchanged text always produces the
same result), and costly (Groq latency, or Ollama's ~100s cold start).
"""

from __future__ import annotations

from src.freep_pipeline.extraction.llm_field_extractor import ExtractedFields
from src.freep_pipeline.models.job import ParsedJob
from src.freep_pipeline.pipeline import ScanPipeline


class _StubFieldExtractor:
    def __init__(self, result: ExtractedFields | None = None) -> None:
        self._result = result or ExtractedFields()
        self.calls = 0

    def extract(self, title, hard_requirements, wishes) -> ExtractedFields:
        self.calls += 1
        return self._result


class _FakeExistingJob:
    """Stand-in for storage.models.JobCurrent with just the fields the
    skip-decision and field-reuse logic read."""

    def __init__(self, source_hash: str | None, **llm_fields) -> None:
        self.source_hash = source_hash
        defaults = dict(
            education=["Old education"],
            experience=["Old experience"],
            skills=["Old skill"],
            methods=["Old method"],
            certifications=["Old cert"],
            languages=["Nederlands"],
            contract_type="detachering",
            zzp_allowed=False,
            screening="VOG vereist",
            vog=True,
            positions=2,
            max_candidates=5,
        )
        defaults.update(llm_fields)
        for key, value in defaults.items():
            setattr(self, key, value)


class _StubRepository:
    def __init__(self, existing: _FakeExistingJob | None) -> None:
        self._existing = existing
        self.calls = 0

    def get_current_job(self, source_job_id: str):
        self.calls += 1
        return self._existing


def _bare_job(**overrides) -> ParsedJob:
    defaults = dict(
        source_job_id="freep-1",
        source_url="https://www.freep.nl/opdracht/1",
        title="Sr IT Architect",
        hard_requirements=["Geen ZZP", "HBO werk- en denkniveau"],
        wishes=["Ervaring met Azure"],
    )
    defaults.update(overrides)
    return ParsedJob(**defaults)


def _pipeline(field_extractor: _StubFieldExtractor, repository: _StubRepository) -> ScanPipeline:
    pipeline = ScanPipeline.__new__(ScanPipeline)  # bypass __init__'s real dependencies
    pipeline._field_extractor = field_extractor
    pipeline._repository = repository
    return pipeline


def test_llm_is_skipped_when_source_hash_matches_the_previous_observation() -> None:
    job = _bare_job()
    source_hash = ScanPipeline._compute_source_hash(job)
    extractor = _StubFieldExtractor()
    repository = _StubRepository(_FakeExistingJob(source_hash=source_hash))
    pipeline = _pipeline(extractor, repository)

    pipeline._enrich_with_llm_fields_unless_source_unchanged(job)

    assert extractor.calls == 0
    assert job.education == ["Old education"]
    assert job.skills == ["Old skill"]
    assert job.zzp_allowed is False
    assert job.vog is True
    assert job.positions == 2


def test_llm_runs_when_source_hash_differs_from_the_previous_observation() -> None:
    job = _bare_job()
    extractor = _StubFieldExtractor(ExtractedFields(skills=["New skill"]))
    repository = _StubRepository(_FakeExistingJob(source_hash="a-completely-different-hash"))
    pipeline = _pipeline(extractor, repository)

    pipeline._enrich_with_llm_fields_unless_source_unchanged(job)

    assert extractor.calls == 1
    assert job.skills == ["New skill"]


def test_llm_runs_for_a_job_never_seen_before() -> None:
    job = _bare_job()
    extractor = _StubFieldExtractor(ExtractedFields(skills=["Fresh extraction"]))
    repository = _StubRepository(existing=None)
    pipeline = _pipeline(extractor, repository)

    pipeline._enrich_with_llm_fields_unless_source_unchanged(job)

    assert extractor.calls == 1
    assert job.skills == ["Fresh extraction"]


def test_llm_runs_when_previous_observation_has_no_source_hash_yet() -> None:
    """A job stored before this optimization existed has source_hash=None
    — must not be treated as "matches", or every pre-existing job would
    silently keep stale/never-extracted LLM fields forever."""
    job = _bare_job()
    extractor = _StubFieldExtractor(ExtractedFields(skills=["Backfilled extraction"]))
    repository = _StubRepository(_FakeExistingJob(source_hash=None))
    pipeline = _pipeline(extractor, repository)

    pipeline._enrich_with_llm_fields_unless_source_unchanged(job)

    assert extractor.calls == 1
    assert job.skills == ["Backfilled extraction"]


def test_source_hash_ignores_llm_derived_fields() -> None:
    """The hash must be computable before the LLM ever runs — two jobs
    identical in every HTML-parsed field but with different (or absent)
    LLM fields must hash the same."""
    plain = _bare_job()
    with_llm_fields = _bare_job()
    with_llm_fields.skills = ["Python"]
    with_llm_fields.zzp_allowed = True

    assert ScanPipeline._compute_source_hash(plain) == ScanPipeline._compute_source_hash(with_llm_fields)


def test_source_hash_changes_when_a_source_field_changes() -> None:
    original = _bare_job()
    changed = _bare_job(title="Different title")

    assert ScanPipeline._compute_source_hash(original) != ScanPipeline._compute_source_hash(changed)
