"""AC04: demonstrates deduplication against a real duplicate case.

Freep's __NUXT_DATA__ payload can reference the same job from more than
one place in the tree (e.g. a "featured" list plus the full listing) —
FreepDiscovery._collect_unique_jobs (called from discover_job_links) must
collapse those into one link, deduplicated by Freep job slug
(DEDUP_RULE in pipeline.py: "unique by Freep job slug").

Builds a real devalue-encoded __NUXT_DATA__ payload (the actual wire
format, not a shortcut) with one job duplicated across two lists, embeds
it in a minimal HTML page, and drives discover_job_links() through its
real HTTP + decode + coverage-check path (only requests.get is mocked).
"""

from __future__ import annotations

import json
from unittest.mock import patch

from src.freep_pipeline.discovery.freep_discovery import FreepDiscovery

ICT_SEGMENT = "ICT Informatievoorziening"


def _nuxt_data_payload_with_duplicate_job() -> list:
    """A devalue-encoded array (flat, index-referenced) where the job at
    index 3 ("job-a-slug") is reachable from both the "featured" list
    (index 1) and the "all_jobs" list (index 2) — the exact duplication
    scenario _collect_unique_jobs's docstring describes."""
    return [
        {"featured": 1, "all_jobs": 2},  # 0: root
        [3],  # 1: featured -> [job A]
        [3, 4],  # 2: all_jobs -> [job A, job B]  (job A referenced twice)
        {"segment": 5, "slug": 6, "title": 7},  # 3: job A
        {"segment": 5, "slug": 8, "title": 9},  # 4: job B
        ICT_SEGMENT,  # 5
        "job-a-slug",  # 6
        "Job A Title",  # 7
        "job-b-slug",  # 8
        "Job B Title",  # 9
    ]


def _html_with_nuxt_data(payload: list, displayed_count: int) -> str:
    nuxt_json = json.dumps(payload)
    return f"""
    <html>
      <body>
        <label for="{ICT_SEGMENT}">{ICT_SEGMENT} ({displayed_count})</label>
        <script id="__NUXT_DATA__" type="application/json">{nuxt_json}</script>
      </body>
    </html>
    """


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text
        self.status_code = 200

    def raise_for_status(self) -> None:
        pass


def test_duplicate_job_reference_is_deduplicated_by_slug() -> None:
    """The same job (same slug) appears twice in the raw NUXT_DATA tree
    (once in "featured", once in "all_jobs"). Discovery must return it
    exactly once — 2 unique jobs, not 3 raw occurrences."""
    payload = _nuxt_data_payload_with_duplicate_job()
    html = _html_with_nuxt_data(payload, displayed_count=2)

    with patch("src.freep_pipeline.discovery.freep_discovery.requests.get", return_value=_FakeResponse(html)):
        result = FreepDiscovery().discover_job_links()

    slugs = sorted(link.source_job_path for link in result.links)
    assert slugs == ["job-a-slug", "job-b-slug"], "duplicate tree reference was not collapsed by slug"
    assert len(result.links) == 2

    # Coverage check: Freep displays "2" (the true unique count), and
    # discovery found 2 unique jobs — matches, despite 3 raw occurrences
    # in the tree (job A counted twice, job B once).
    assert result.coverage_confirmed is True
    assert result.displayed_count == 2


def test_duplicate_job_reference_produces_no_duplicate_urls() -> None:
    """Every discovered link must point to a distinct job URL — the
    explainable dedup rule (AC04) has no effect if two RawJobLinks for the
    same slug slip through with different casing/paths."""
    payload = _nuxt_data_payload_with_duplicate_job()
    html = _html_with_nuxt_data(payload, displayed_count=2)

    with patch("src.freep_pipeline.discovery.freep_discovery.requests.get", return_value=_FakeResponse(html)):
        result = FreepDiscovery().discover_job_links()

    urls = [link.source_url for link in result.links]
    assert len(urls) == len(set(urls)), f"duplicate URLs leaked through: {urls}"


def test_job_outside_ict_segment_is_excluded_even_if_duplicated() -> None:
    """A non-ICT job duplicated across the tree must not appear at all —
    proves the segment filter and the dedup-by-slug logic compose
    correctly rather than one bypassing the other."""
    payload = _nuxt_data_payload_with_duplicate_job()
    # Add a duplicated non-ICT job (indices 10-13) referenced from both
    # lists at indices 1 and 2.
    payload[1].append(10)
    payload[2].append(10)
    payload.extend(
        [
            {"segment": 11, "slug": 12, "title": 13},  # 10: non-ICT job, duplicated
            "Finance",  # 11
            "finance-job-slug",  # 12
            "Finance Job",  # 13
        ]
    )
    html = _html_with_nuxt_data(payload, displayed_count=2)

    with patch("src.freep_pipeline.discovery.freep_discovery.requests.get", return_value=_FakeResponse(html)):
        result = FreepDiscovery().discover_job_links()

    slugs = {link.source_job_path for link in result.links}
    assert "finance-job-slug" not in slugs
    assert slugs == {"job-a-slug", "job-b-slug"}
