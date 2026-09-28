# Freep ICT Job Pipeline — Backend

Discovers, fetches, parses, validates and stores ICT job listings from
Freep. See `../freep-ict-job-pipeline/CLAUDE.md` for the full data
contract and API surface this backend must implement.

## Structure

```text
config/                   centralized settings + logging
src/freep_pipeline/
  discovery/               find job links on Freep (crawl4ai)
  fetching/                fetch a job detail page (requests)
  parsing/                 extract structured fields from HTML
  normalization/           derive structured values from free text
  validation/              quality checks before storage
  tracking/                derive change_type across scans
  storage/                 PostgreSQL models + repository
  models/                  Pydantic domain models
  pipeline.py              orchestrates one full scan run
scripts/                   CLI entry points
tests/                     pytest tests
```

## Setup

See commands given at the end of the backend build conversation:
create the venv, install `requirements.txt`, copy `.env.example` to
`.env`, start PostgreSQL, run `pytest`, then `scripts/scrape.py`.

## Logging

All logs go to `logs/pipeline.log` (created on first run) and the
console. No `print()` in application code — use
`config.logging_config.get_logger(__name__)`.
