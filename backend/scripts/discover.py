"""CLI entry point: run discovery only, print the number of jobs found.

Usage:
    python scripts/discover.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config.logging_config import get_logger
from src.freep_pipeline.discovery.freep_discovery import FreepDiscovery

logger = get_logger(__name__)


async def main() -> None:
    discovery = FreepDiscovery()
    links = await discovery.discover_job_links()
    logger.info("Discovered %d unique ICT job links", len(links))
    for link in links:
        logger.info("  %s", link.source_url)


if __name__ == "__main__":
    asyncio.run(main())
