# Freep ICT Job Pipeline — Backend

Discovers, fetches, parses, validates and stores ICT job listings from
Freep. See `../freep-ict-job-pipeline/CLAUDE.md` for the full data
contract and API surface this backend must implement.

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

## Auth (Keycloak)

The API (`src/freep_pipeline/api/`) verifies a Keycloak-issued JWT
(signature, expiration, issuer, audience) on every job endpoint —
`GET /api/v1/health` is the only unauthenticated route.

1. Start Keycloak:

   ```bash
   docker run -d --name freep-keycloak -p 8080:8080 \
     -e KEYCLOAK_ADMIN=admin -e KEYCLOAK_ADMIN_PASSWORD=admin \
     quay.io/keycloak/keycloak:25.0 start-dev
   ```

2. Create a realm named `dreev`.
3. Create a client `freep-pipeline-api` (confidential, no standard flow,
   no direct access grants, no service account) — this is the resource
   server the API identifies itself as; it never itself requests tokens.
4. Create a client `freep-test-client` (confidential, service accounts
   enabled) for the independent test client (AC15) to authenticate as via
   the `client_credentials` grant. Add an audience mapper
   (`oidc-audience-mapper`, `included.client.audience=freep-pipeline-api`)
   so its tokens carry the right `aud` claim.
5. Set `KEYCLOAK_ISSUER_URL` / `KEYCLOAK_API_AUDIENCE` in `.env` (see
   `.env.example`), and `FREEP_TEST_CLIENT_ID` / `FREEP_TEST_CLIENT_SECRET`
   for the test client.

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
