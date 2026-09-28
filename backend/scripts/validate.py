"""CLI entry point: fetch+parse a single job URL and validate it, without
storing anything. Useful to sanity-check the parser against one page.

Usage:
    python scripts/validate.py https://www.freep.nl/opdracht/ai-developer-1
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config.logging_config import get_logger
from src.freep_pipeline.fetching.http_client import FreepHttpClient
from src.freep_pipeline.parsing.job_parser import JobParser
from src.freep_pipeline.validation.validator import JobValidator

logger = get_logger(__name__)


def main(url: str) -> None:
    client = FreepHttpClient()
    parser = JobParser()
    validator = JobValidator()

    soup = client.get_detail_soup(url)
    job = parser.parse(soup, url)

    logger.info("Parsed job: %s", job.model_dump_json(indent=2))

    results = validator.validate_batch([job])
    result = results[0]

    if result.is_valid:
        logger.info("Job is valid")
    else:
        logger.warning("Job failed validation: %s", result.errors)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/validate.py <job_url>")
        sys.exit(1)

    main(sys.argv[1])
