"""Tests for JobParser against a fixed HTML fixture.

Migrated from the notebook's single-job smoke test (cell 26), turned into
a fixture-based test so it does not depend on network access or on Freep's
live HTML.
"""

from bs4 import BeautifulSoup

from freep_pipeline.parsing.job_parser import JobParser

FIXTURE_HTML = """
<html>
  <body>
    <a href="/detachering" class="text-center leading-6 font-medium xl:text-lg text-indigo-600">Detachering</a>
    <h1>AI Developer</h1>
    <p>Acme Consulting</p>
    <span class="lg:fixed lg:top-4 lg:right-4 flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium whitespace-nowrap bg-pink-50 text-pink-800">detachering</span>
    <ul class="mt-8">
      <li>Utrecht</li>
      <li>&euro;80 - 100 per uur</li>
      <li>32 - 40 uur per week</li>
      <li><a href="/opdrachten/ict">ICT Informatievoorziening</a></li>
      <li>18 September 2026</li>
      <li>18 December 2026</li>
    </ul>
    <h2>Over de opdracht</h2>
    <div class="prose-base">Build and maintain AI-powered tooling.</div>
    <h4>De eisen</h4>
    <ul>
      <li>Minimum 5 years of experience with Python</li>
      <li>Knowledge of SQL</li>
    </ul>
    <h4>De wensen</h4>
    <ul>
      <li>Experience with Power BI is a plus</li>
    </ul>
  </body>
</html>
"""

URL = "https://www.freep.nl/opdracht/ai-developer-1"


def test_parse_job_detail_extracts_expected_fields():
    soup = BeautifulSoup(FIXTURE_HTML, "html.parser")
    parser = JobParser()

    job = parser.parse(soup, URL)

    assert job.source_job_id == "ai-developer-1"
    assert job.title == "AI Developer"
    assert job.company == "Acme Consulting"
    assert job.province == "Utrecht"
    assert job.segment == "ICT Informatievoorziening"
    assert job.hours_per_week == "32 - 40 uur per week"
    assert job.start_date == "18 September 2026"
    assert job.end_date == "18 December 2026"
    assert job.description_original == "Build and maintain AI-powered tooling."
    assert job.hard_requirements == [
        "Minimum 5 years of experience with Python",
        "Knowledge of SQL",
    ]
    assert job.wishes == ["Experience with Power BI is a plus"]
    assert job.contract_type == "detachering"


def test_parse_job_detail_handles_missing_sections():
    soup = BeautifulSoup("<html><body><h1>Minimal Job</h1></body></html>", "html.parser")
    parser = JobParser()

    job = parser.parse(soup, URL)

    assert job.title == "Minimal Job"
    assert job.hard_requirements == []
    assert job.wishes == []
    assert job.description_original is None
    assert job.contract_type is None


def test_contract_type_badge_is_not_confused_with_the_site_navigation_link():
    """The pill-shaped <span> badge is the per-offer contract type;
    <a href="/detachering">Detachering</a> is unrelated site navigation
    that happens to share the same word — only the span must be read."""
    soup = BeautifulSoup(
        """
        <html><body>
          <a href="/freelance">Freelance</a>
          <h1>Production engineer</h1>
          <span class="px-2.5 py-0.5 rounded-full text-xs bg-pink-50 text-pink-800">freelance</span>
        </body></html>
        """,
        "html.parser",
    )
    parser = JobParser()

    job = parser.parse(soup, URL)

    assert job.contract_type == "freelance"
