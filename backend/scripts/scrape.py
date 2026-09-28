"""CLI entry point: run one full scan (discover, fetch, parse, validate,
store in PostgreSQL).

Usage:
    python scripts/scrape.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config.logging_config import get_logger
from freep_pipeline.pipeline import ScanPipeline

logger = get_logger(__name__)


async def main() -> None:
    pipeline = ScanPipeline()
    scan_id = await pipeline.run()
    logger.info("Scan complete: %s", scan_id)


if __name__ == "__main__":
    asyncio.run(main())
