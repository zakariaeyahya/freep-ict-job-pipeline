"""Verifies ScanPipeline actually wires LlmFieldExtractor's output onto
each ParsedJob before storage (pipeline.py's _enrich_with_llm_fields) —
the connection point between the extractor (tested in isolation in
test_llm_field_extractor.py) and the rest of the pipeline.
"""

from __future__ import annotations

from src.freep_pipeline.extraction.llm_field_extractor import ExtractedFields
from src.freep_pipeline.models.job import ParsedJob
from src.freep_pipeline.pipeline import ScanPipeline


class _StubFieldExtractor:
    def __init__(self, result: ExtractedFields) -> None:
        self._result = result
        self.calls: list[tuple[str, list[str], list[str]]] = []

    def extract(self, title, hard_requirements, wishes) -> ExtractedFields:
        self.calls.append((title, hard_requirements, wishes))
        return self._result


def _bare_job() -> ParsedJob:
    return ParsedJob(
        source_job_id="freep-1",
        source_url="https://www.freep.nl/opdracht/1",
        title="Sr IT Architect",
        hard_requirements=["Geen ZZP", "HBO werk- en denkniveau"],
        wishes=["Ervaring met Azure"],
    )


def test_enrich_with_llm_fields_copies_every_extracted_field_onto_the_job() -> None:
    extracted = ExtractedFields(
        education=["HBO werk- en denkniveau"],
        experience=["5 jaar ervaring"],
        skills=["Azure"],
        methods=["Scrum"],
        certifications=["AZ-900"],
        languages=["Nederlands"],
        contract_type="detachering",
        zzp_allowed=False,
        screening="VOG vereist",
        vog=True,
        positions=2,
        max_candidates=5,
    )
    pipeline = ScanPipeline.__new__(ScanPipeline)  # bypass __init__'s real dependencies
    pipeline._field_extractor = _StubFieldExtractor(extracted)
    job = _bare_job()

    pipeline._enrich_with_llm_fields(job)

    assert job.education == ["HBO werk- en denkniveau"]
    assert job.experience == ["5 jaar ervaring"]
    assert job.skills == ["Azure"]
    assert job.methods == ["Scrum"]
    assert job.certifications == ["AZ-900"]
    assert job.languages == ["Nederlands"]
    assert job.contract_type == "detachering"
    assert job.zzp_allowed is False
    assert job.screening == "VOG vereist"
    assert job.vog is True
    assert job.positions == 2
    assert job.max_candidates == 5


def test_enrich_with_llm_fields_passes_the_job_title_and_lists_to_the_extractor() -> None:
    stub = _StubFieldExtractor(ExtractedFields())
    pipeline = ScanPipeline.__new__(ScanPipeline)
    pipeline._field_extractor = stub
    job = _bare_job()

    pipeline._enrich_with_llm_fields(job)

    assert stub.calls == [("Sr IT Architect", ["Geen ZZP", "HBO werk- en denkniveau"], ["Ervaring met Azure"])]


def test_enrich_with_llm_fields_leaves_job_at_defaults_when_nothing_is_extracted() -> None:
    pipeline = ScanPipeline.__new__(ScanPipeline)
    pipeline._field_extractor = _StubFieldExtractor(ExtractedFields())
    job = _bare_job()

    pipeline._enrich_with_llm_fields(job)

    assert job.education == []
    assert job.contract_type is None
    assert job.zzp_allowed is None
