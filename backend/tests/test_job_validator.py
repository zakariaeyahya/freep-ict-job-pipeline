"""AC04 (second layer): even if two distinct fetched pages somehow produced
the same source_job_id (e.g. a link discovered twice with a trailing-slash
variant, or a future route overlapping with the current one),
JobValidator._validate_duplicate_id is the safety net that catches it
after parsing — independent of FreepDiscovery's own dedup-by-slug
(covered in test_freep_discovery.py).
"""

from __future__ import annotations

from src.freep_pipeline.models.job import ParsedJob
from src.freep_pipeline.validation.validator import JobValidator


def _valid_job(source_job_id: str, source_url: str) -> ParsedJob:
    return ParsedJob(
        source_job_id=source_job_id,
        source_url=source_url,
        title="AI Developer",
        company="Acme Consulting",
        description_original="Build and maintain tooling.",
        segment="ICT Informatievoorziening",
    )


def test_duplicate_source_job_id_is_flagged_on_the_second_occurrence() -> None:
    """Two parsed jobs sharing the same source_job_id (as if the same job
    had been fetched twice under two different URLs): the first occurrence
    is valid, the second is rejected as a duplicate — never both silently
    accepted and stored twice."""
    first = _valid_job("freep-12345", "https://www.freep.nl/opdracht/ai-developer-1")
    duplicate = _valid_job("freep-12345", "https://www.freep.nl/opdracht/ai-developer-1/")

    results = JobValidator().validate_batch([first, duplicate])

    assert results[0].is_valid
    assert not results[1].is_valid
    assert any("duplicate source_job_id: freep-12345" in error for error in results[1].errors)


def test_distinct_source_job_ids_are_both_valid() -> None:
    """Control case: two genuinely different jobs must not be flagged as
    duplicates of each other."""
    job_a = _valid_job("freep-11111", "https://www.freep.nl/opdracht/job-a")
    job_b = _valid_job("freep-22222", "https://www.freep.nl/opdracht/job-b")

    results = JobValidator().validate_batch([job_a, job_b])

    assert results[0].is_valid
    assert results[1].is_valid


def test_three_way_duplicate_flags_second_and_third_occurrence() -> None:
    """Three parsed jobs with the same id: only the first is accepted, the
    other two are both flagged — the dedup rule doesn't stop after
    catching just one repeat."""
    jobs = [_valid_job("freep-99999", f"https://www.freep.nl/opdracht/variant-{i}") for i in range(3)]

    results = JobValidator().validate_batch(jobs)

    assert results[0].is_valid
    assert not results[1].is_valid
    assert not results[2].is_valid
