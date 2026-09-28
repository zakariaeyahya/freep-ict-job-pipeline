"""Centralized configuration for the Freep ICT job pipeline.

All constants and environment-derived settings live here. Nothing else in
the codebase should read os.environ directly or hardcode a URL, selector,
timeout, or file path — import from this module instead.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "pipeline.log"
DATA_DIR = BASE_DIR / "data"

# --------------------------------------------------------------------------
# Freep source
# --------------------------------------------------------------------------

FREEP_BASE_URL = "https://www.freep.nl"
FREEP_START_URL = "https://www.freep.nl/"
ICT_FILTER_LABEL = "ICT Informatievoorziening"
JOB_LINK_MARKER = "/opdracht/"

HTTP_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/154.0.0.0 Safari/537.36"
)
HTTP_TIMEOUT_SECONDS = 30
HTTP_REQUEST_DELAY_SECONDS = 0.5

BROWSER_HEADLESS = True
BROWSER_PAGE_TIMEOUT_MS = 30_000

KNOWN_PROVINCES = [
    "Gelderland",
    "Zuid-Holland",
    "Utrecht",
    "Noord-Holland",
    "Noord-Brabant",
    "Overijssel",
    "Drenthe",
    "Friesland",
    "Zeeland",
    "Groningen",
    "Flevoland",
]

# --------------------------------------------------------------------------
# Database (PostgreSQL, image postgres:17-alpine)
# --------------------------------------------------------------------------

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://freep:freep@localhost:5432/freep_pipeline",
)

# --------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
