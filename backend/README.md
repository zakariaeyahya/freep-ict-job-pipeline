# Freep ICT Job Pipeline — Backend

Discovers, fetches, parses, validates and stores ICT job listings from
Freep. See `../freep-ict-job-pipeline/CLAUDE.md` for the full data
contract and API surface this backend must implement,
[`../docs/DISCOVERY_REPORT.md`](../docs/DISCOVERY_REPORT.md) for the source analysis,
robots.txt/terms-of-use review, and open legal/operational questions
(brief §9.1, §7), [`RUNBOOK.md`](RUNBOOK.md) for installation/operations,
and [`SOLUTION_PROPOSAL.md`](SOLUTION_PROPOSAL.md) for the scan-worker
architecture decision.

## Structure

```text
config/                   centralized settings + logging
contracts/                 versioned JSON Schema (AC12) + required fixtures
src/freep_pipeline/
  discovery/               find job links on Freep (crawl4ai)
  fetching/                fetch a job detail page (requests)
  parsing/                 extract structured fields from HTML
  normalization/           derive structured values from free text
  validation/              quality checks before storage
  tracking/                derive change_type across scans
  storage/                 PostgreSQL models + repository
  contracts/               JobRecord mapper + JSON Schema validator (AC12/AC14)
  extraction/              LLM-assisted profile/engagement/procedure extraction (OpenAI/Groq)
  api/                     FastAPI app: /api/v1 routes, services, JWT auth
  models/                  Pydantic domain models
  pipeline.py              orchestrates one full scan run
scripts/                   CLI entry points
tests/                     pytest tests
  test_client/             AC15 independent test client + its own test
```

## Setup

Create the venv, install `requirements.txt`, copy `.env.example` to
`.env`, start PostgreSQL, run `pytest`, then `scripts/scrape.py`.

## Run the full stack with Docker

From the repository root, copy `.env.example` to `.env`, replace the
passwords/secrets, then build and start the containers:

```bash
docker compose up --build
```

The frontend is at http://localhost:3000, the API at
http://localhost:8000, and the Keycloak admin console at
http://localhost:8080. PostgreSQL and Keycloak data persist in Docker
volumes. No manual Keycloak setup is needed — the `dreev` realm and its
clients import automatically and the `keycloak-init` service pushes the
secrets from `.env`; see "Auth (Keycloak)" below. The API uses
`http://keycloak:8080/realms/dreev` as the issuer inside the Compose
network.

Stop the containers with `docker compose down`; add `-v` only when you
intentionally want to delete the persisted database and Keycloak data.

### Publish the application images to Docker Hub

Set `DOCKERHUB_USERNAME` and `IMAGE_TAG` in the root `.env`, then log in
and publish only the two application images (not PostgreSQL or Keycloak):

```bash
docker login
docker compose build backend frontend
docker compose push backend frontend
```

On another machine, pull and start them with the same Compose file and a
configured `.env`:

```bash
docker compose pull backend frontend
docker compose up -d
```

For deployment on a different domain, set `NEXT_PUBLIC_API_BASE_URL` to
the public API URL before building the frontend image and rebuild it;
this value is embedded in the browser bundle at build time.

## API surface

| Endpoint | Description |
| --- | --- |
| `GET /api/v1/jobs` | Paginated job list, filterable by `status`/`change_type` |
| `GET /api/v1/jobs/{internal_job_id}` | One job's current published record |
| `GET /api/v1/jobs/{internal_job_id}/versions` | Past observations of one job (excludes the current state) |
| `GET /api/v1/scans` | Paginated scan run list, most recent first |
| `GET /api/v1/scans/{scan_id}` | One scan run's full report |
| `POST /api/v1/scans/trigger` | Starts a scan on a background thread, returns `202` immediately (409 if one is already running) |
| `GET /api/v1/exports/{scan_id}.jsonl` | One schema-validated `JobRecord` per line, UTF-8, for every job observed during that scan |
| `GET /api/v1/health` | Liveness + freshness of the last published scan (unauthenticated) |

Every job/scan response is schema-validated (AC12) before it leaves the
API. `convergence_rounds` on a `ScanRun` is always `[]` — convergence
rounds are not modeled yet (only one known source route today).

## LLM-assisted extraction (profile/engagement/procedure)

Freep exposes education/experience/skills/screening/zzp_allowed/etc. only
as prose mixed into the eisen/wensen lists, not as separate HTML fields —
`LlmFieldExtractor` (`src/freep_pipeline/extraction/`) classifies these
from the source text. Every value it returns is verified to be an exact
substring of the source before being trusted (never a paraphrase or
invention — see the module's docstring for the anti-fabrication guarantee).
`contract_type` ("detachering"/"freelance") is extracted separately by
`JobParser` from a real HTML badge and always takes priority over the
LLM's guess when present.

`FallbackLlmClient` tries OpenAI first (needs `OPENAI_API_KEY`), falling
back to Groq (`GROQ_API_KEY`) if OpenAI is unavailable. There is no local
fallback — on a CPU-only host a local model's response time can dominate
a scan's wall-clock time, so extraction here is OpenAI-or-Groq-or-nothing
(brief's "never blocks a scan" rule for best-effort extraction).

Set `OPENAI_API_KEY` / `OPENAI_MODEL` and `GROQ_API_KEY` / `GROQ_MODEL` in
`.env` (see `.env.example`). Extraction is best-effort: if both providers
are unavailable, the scan continues and these fields are simply left
empty for that job — never blocks a scan.

Manual one-job sanity check against a real sample (never run against the
full dataset — costs time/quota):

```bash
python scripts/test_llm_extraction.py --provider fallback  # or openai / groq
```

## Auth (Keycloak)

The API (`src/freep_pipeline/api/`) verifies a Keycloak-issued JWT
(signature, expiration, issuer, audience) on every job/scan/export
endpoint — `GET /api/v1/health` is the only unauthenticated route.

The `dreev` realm and its three clients are defined in
[`../docker/keycloak/dreev-realm.json`](../docker/keycloak/dreev-realm.json)
and import automatically the first time the `keycloak` container starts
(`--import-realm`), so no manual admin-console setup is needed on any
machine:

- **`freep-pipeline-api`** — confidential, no standard flow, no direct
  access grants, no service account. The resource server the API
  identifies itself as; it never itself requests tokens.
- **`freep-test-client`** — confidential, service accounts enabled, for
  the independent test client (AC15) to authenticate via
  `client_credentials`. Carries an audience mapper
  (`included.client.audience=freep-pipeline-api`) so its tokens have the
  right `aud` claim.
- **`freep-reviewer-ui`** — confidential, **Direct Access Grants only**
  (this is what allows the ROPC grant, `grant_type=password`, the login
  endpoint uses — the UI never redirects to Keycloak directly, only the
  backend talks to it), with the same audience mapper already attached.
  Without it, tokens from this client would carry `aud: "account"`
  (Keycloak's default) and every protected endpoint would reject them
  with 401 — a real pitfall hit during initial setup, now baked into the
  committed realm JSON so it can't recur.

Right after Keycloak imports the realm, the `keycloak-init` service (see
[`../docker/keycloak/init-secrets.sh`](../docker/keycloak/init-secrets.sh))
runs once and:

1. Sets `freep-reviewer-ui` and `freep-test-client`'s secrets from
   `KEYCLOAK_REVIEWER_CLIENT_SECRET` / `FREEP_TEST_CLIENT_SECRET` in
   `.env` — the committed realm JSON never contains real secrets
   (Keycloak strips them from any export).
2. Creates (or updates) a reviewer user from `REVIEWER_USERNAME` /
   `REVIEWER_PASSWORD` / `REVIEWER_EMAIL` in `.env`, with email verified,
   first/last name set, and a non-temporary password — all the fields
   Keycloak's ROPC grant silently requires for an account to count as
   "fully set up" (a user missing any of these fails with the same opaque
   `invalid_grant` error as a wrong password, which cost real debugging
   time before this was automated).

Both steps are idempotent: restarting the stack or redeploying to a new
machine never repeats manual setup — it only needs a `.env` with the
right secrets (see `.env.example` at the repo root).

Quick way to verify a user/client pair works:

```bash
curl -s -X POST http://localhost:8080/realms/dreev/protocol/openid-connect/token \
  -d grant_type=password -d client_id=freep-reviewer-ui \
  -d client_secret=<KEYCLOAK_REVIEWER_CLIENT_SECRET> \
  -d username=<REVIEWER_USERNAME> -d password=<REVIEWER_PASSWORD> -d scope=openid
```

A real `access_token` in the response means Keycloak is fully set up; an
`invalid_grant`/`invalid_client` error means a `.env` value is out of
sync with what `keycloak-init` actually pushed (check
`docker compose logs keycloak-init`), not the API code.

## CORS

The review UI runs on a different origin (`http://localhost:3000` by
default) than this API (`http://localhost:8000`), so the browser sends a
CORS preflight (`OPTIONS`) before every cross-origin request — including
login. `CORS_ALLOWED_ORIGINS` in `.env` (comma-separated, never `*` per
CLAUDE.md) controls which origins are allowed; update it if the frontend
is served from somewhere else.

## Running the API

```bash
uvicorn src.freep_pipeline.api.main:app --reload
```

## AC15: independent test client

`tests/test_client/independent_test_client.py` is a standalone script —
it imports nothing from `freep_pipeline`, only `httpx` — that gets its own
access token from Keycloak and reads `/api/v1/jobs` and `/api/v1/health`
as plain JSON. Run it against a live API + Keycloak with:

```bash
python tests/test_client/independent_test_client.py
```

The same HTTP contract is also exercised automatically in
`tests/test_client/test_independent_client_reads_api.py` (via FastAPI's
`TestClient`, no live server needed for `pytest`).

## Logging

All logs go to `logs/pipeline.log` (created on first run) and the
console. No `print()` in application code — use
`config.logging_config.get_logger(__name__)`.
