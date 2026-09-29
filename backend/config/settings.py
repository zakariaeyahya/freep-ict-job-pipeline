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

# Freep's homepage response intermittently omits the ICT filter count label
# (observed: same URL, same headers, HTTP 200, full job list present, but
# the label text missing from that particular response) even though a
# request moments later has it. Re-fetching the homepage — not re-parsing
# the same HTML — resolves it in practice, so the coverage check retries a
# fresh request this many times before giving up (brief §3.3: a local/
# transient problem must not unnecessarily block the entire run).
HOMEPAGE_COVERAGE_RETRY_ATTEMPTS = 3
HOMEPAGE_COVERAGE_RETRY_DELAY_SECONDS = 2

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

KEYCLOAK_TOKEN_URL = f"{KEYCLOAK_ISSUER_URL}/protocol/openid-connect/token"

# Client used for the human login endpoint (POST /api/v1/auth/login),
# distinct from freep-pipeline-api (the resource server, which cannot
# itself request tokens) and freep-test-client (service account, AC15).
# Must have "Direct Access Grants" enabled in Keycloak (Resource Owner
# Password Credentials grant) — the API forwards the caller's email/
# password to Keycloak and never stores or checks a password itself.
KEYCLOAK_REVIEWER_CLIENT_ID = os.environ.get("KEYCLOAK_REVIEWER_CLIENT_ID", "freep-reviewer-ui")
KEYCLOAK_REVIEWER_CLIENT_SECRET = os.environ.get("KEYCLOAK_REVIEWER_CLIENT_SECRET", "")

# --------------------------------------------------------------------------
# CORS
# --------------------------------------------------------------------------

# The review UI (freep-ict-job-pipeline, a separate Next.js app/origin)
# calls this API from the browser — comma-separated, never "*"
# (CLAUDE.md: "Configure CORS per allowed origin, never `*`").
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

# --------------------------------------------------------------------------
# LLM field extraction (OpenAI primary, Groq fallback)
# --------------------------------------------------------------------------

# Extracts profile/engagement/procedure signals (brief §4.2) from free-text
# requirements/wishes/description that the HTML parser cannot reliably
# split into structured fields (e.g. "Geen ZZP", "afgeronde HBO opleiding"
# are prose, not separate HTML elements).

# OPENAI_API_KEY is a real secret — env var only, never committed, never
# logged.
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TIMEOUT_SECONDS = 60

# --------------------------------------------------------------------------
# Groq (fallback when OpenAI is unavailable)
# --------------------------------------------------------------------------

# GROQ_API_KEY is a real secret — env var only, never committed, never
# logged.
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_TIMEOUT_SECONDS = 60
