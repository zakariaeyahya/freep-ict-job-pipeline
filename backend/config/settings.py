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

# A job absent from CLOSURE_AFTER_CONSECUTIVE_ABSENCES consecutive scans
# is marked closed. A single miss only ever becomes temporarily_not_found
# (brief §3.3: "Do not automatically treat a single instance of not
# finding an assignment as a deletion").
CLOSURE_AFTER_CONSECUTIVE_ABSENCES = 2

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

# --------------------------------------------------------------------------
# Auth (Keycloak, image quay.io/keycloak/keycloak:25.0)
# --------------------------------------------------------------------------

# The realm's issuer URL. Every access token's `iss` claim must match this
# exactly, and the JWKS used to verify signatures is fetched from here.
KEYCLOAK_ISSUER_URL = os.environ.get("KEYCLOAK_ISSUER_URL", "http://localhost:8080/realms/dreev")
KEYCLOAK_JWKS_URL = f"{KEYCLOAK_ISSUER_URL}/protocol/openid-connect/certs"

# The client_id this API represents as a resource server. Every access
# token's `aud` claim must include this value, or the token was not
# actually issued for this API and must be rejected.
KEYCLOAK_API_AUDIENCE = os.environ.get("KEYCLOAK_API_AUDIENCE", "freep-pipeline-api")

# --------------------------------------------------------------------------
# LLM field extraction (Ollama, image ollama/ollama:latest, local — no
# secrets leave the machine)
# --------------------------------------------------------------------------

# Extracts profile/engagement/procedure signals (brief §4.2) from free-text
# requirements/wishes/description that the HTML parser cannot reliably
# split into structured fields (e.g. "Geen ZZP", "afgeronde HBO opleiding"
# are prose, not separate HTML elements). Runs locally, never sends job
# text to a third-party API.
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b-instruct")
OLLAMA_TIMEOUT_SECONDS = 60
