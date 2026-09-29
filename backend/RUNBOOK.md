# Runbook — Freep ICT Job Pipeline

Operational guide for installing, configuring, running, monitoring, and
recovering the pipeline (brief §9.1: "Runbook for installation,
configuration, monitoring, recovery and source changes"). For the data
contract and API surface, see `../freep-ict-job-pipeline/CLAUDE.md`. For
the discovery findings and legal/operational risks, see
[`../docs/DISCOVERY_REPORT.md`](../docs/DISCOVERY_REPORT.md). For
architectural alternatives considered, see
[`SOLUTION_PROPOSAL.md`](SOLUTION_PROPOSAL.md).

## 1. Installation

Prerequisites: Docker + the Docker Compose plugin, a Freep-reachable
network connection. Running the full stack (PostgreSQL, Keycloak,
backend, frontend) via `docker compose` from the repo root is the
supported path — see [`../HOSTINGER_DEPLOY.md`](../HOSTINGER_DEPLOY.md)
and the root `.env.example`.

```bash
cd /path/to/repo/root
cp .env.example .env   # fill in secrets — see §2
docker compose up -d --build
```

No manual Keycloak setup is needed: the `dreev` realm and its three
clients (`freep-pipeline-api`, `freep-reviewer-ui`, `freep-test-client`,
audience mapper already attached) import automatically on first Keycloak
startup from
[`../docker/keycloak/dreev-realm.json`](../docker/keycloak/dreev-realm.json).
Right after, the `keycloak-init` service runs once and pushes the client
secrets and the reviewer user/password from `.env` into that realm — see
[`../docker/keycloak/init-secrets.sh`](../docker/keycloak/init-secrets.sh).
Both steps are idempotent, so a restart or redeploy never repeats the
setup or requires the admin console.

Apply the database schema (never hand-edit the schema — see §5):

```bash
docker compose exec backend alembic upgrade head
```

Verify the install:

```bash
docker compose exec backend pytest
```

## 2. Configuration

All configuration is environment variables read once in
`config/settings.py` — nothing else in the codebase reads `os.environ`
directly or hardcodes a URL/secret. `.env.example` documents every
variable with a dummy value; `.env` (never committed) holds the real
ones. Key groups:

| Group | Variables | Notes |
| --- | --- | --- |
| Database | `DATABASE_URL` | PostgreSQL only in production; SQLite is test-only (see `tests/test_scan_recovery.py`) |
| Keycloak | `KEYCLOAK_REVIEWER_CLIENT_SECRET`, `FREEP_TEST_CLIENT_SECRET`, `REVIEWER_USERNAME`/`_PASSWORD`/`_EMAIL` | Realm/clients auto-import — see §1; these are only the secrets pushed in by `keycloak-init` |
| CORS | `CORS_ALLOWED_ORIGINS` | Comma-separated, never `*` |
| LLM extraction | `OPENAI_API_KEY`/`OPENAI_MODEL`, `GROQ_API_KEY`/`GROQ_MODEL` | OpenAI primary, Groq fallback. Best-effort; a scan proceeds even if both are unreachable (see §3) |

Config changes take effect on process restart only — `.env` is loaded
once at import time (`load_dotenv()`), not watched for changes.

## 3. Running a scan

Two ways to start a scan, both going through the same `ScanPipeline`:

- **CLI** (for local development, cron, or any external scheduler):

  ```bash
  .venv/Scripts/python.exe scripts/scrape.py
  ```

- **Manual trigger from the review UI**: the "Run scan now" button on the
  Scan Report page (`POST /api/v1/scans/trigger`) starts a scan on a
  background thread and returns immediately (`202`); the page polls and
  updates itself once the scan finishes. This is the brief §9.2
  "Scheduler: starts... manual scans" responsibility.

Either way, a scan is: discover → fetch → parse → validate → store →
publish (or block publication — see §4). Two scans can never run
concurrently against the same database — `storage/scan_lock.py` takes a
PostgreSQL advisory lock for the duration of the run; a second attempt
fails fast with `ScanAlreadyRunningError` (surfaced as HTTP 409 from the
trigger endpoint) instead of corrupting data. The lock releases itself
automatically if the process crashes (Postgres ties it to the connection,
not to any application-level cleanup), so there is nothing to manually
unstick after a crash.

- `scripts/discover.py` runs discovery only (no fetch/store) — useful to
  sanity-check route coverage without a full scan.
- `scripts/validate.py <job_url>` fetches and validates a single job page
  without storing anything — useful to debug one URL.
- `scripts/test_llm_extraction.py [--provider fallback|groq|openai]` is a
  one-job manual sanity check for the LLM extraction step — never run it
  against the full dataset (time/API quota cost).

## 4. Monitoring

- **`GET /api/v1/health`** (unauthenticated) is the primary freshness
  signal: `seconds_since_last_successful_scan` against the agreed scan
  frequency (`AGREED_SCAN_FREQUENCY_HOURS` in the frontend's
  `lib/contracts/health.ts`, currently 24h — not yet formalized by Dreev,
  see "Known limitations"). It only ever reports a *published*
  (`COMPLETE_WITHIN_SCAN_WINDOW`) scan — an `INCOMPLETE`/`FAILED` run
  never makes the dataset look fresher than it is.
- **`GET /api/v1/scans`** / **`GET /api/v1/scans/{scan_id}`** give the
  full scan report: route-by-route results, counts, errors with
  retry/recovery status, and `published.reason` when publication was
  blocked.
- **Logs**: `logs/pipeline.log` (created on first run) plus console —
  every module logs through `config.logging_config.get_logger(__name__)`,
  never `print()`.
- **A scan's `published` flag is the single source of truth** for whether
  its data is safe to consume: `false` means either the scan itself was
  incomplete (AC11) or a published record failed schema validation
  (AC12/AC14) — check `published.reason` and the scan's `errors[]` first
  when investigating.

There is no automated alerting yet (no email/Slack notification on a
stale or failed scan) — monitoring today is pull-based (poll `/health` or
`/scans`), not push-based. See "Known limitations".

## 5. Recovery

**Interrupted scan (mid-run crash, network failure, process killed):**
Nothing manual is required. Re-running `scripts/scrape.py` is always
safe:

- `job_observations` is append-only — a partial scan's rows are never
  rolled back or duplicated on re-run (each observation is a fresh insert
  keyed by `scan_id` + `source_job_id`, not an upsert).
- `jobs_current` is a derived projection — the next successful scan
  overwrites it correctly regardless of how the previous scan ended.
- A job whose fetch failed mid-scan becomes `temporarily_not_found`, never
  silently dropped or wrongly marked `closed` (a job only closes after
  `CLOSURE_AFTER_CONSECUTIVE_ABSENCES`, currently 2, consecutive misses —
  brief §3.3).
- This exact scenario (interrupt mid-scan, resume, verify zero duplicates
  and zero silent loss) is what `tests/test_scan_recovery.py` proves
  automatically (AC10).

**Corrupted/out-of-sync database schema:** never hand-edit the schema.
Check `alembic current` against `alembic heads`; if behind, `alembic
upgrade head`. If the SQLAlchemy models and the migration history have
drifted (a column was added to a model without a matching migration),
`tests/test_migrations.py::test_current_migration_matches_the_sqlalchemy_models`
will fail — run `alembic revision --autogenerate` and review the
generated migration before applying it (check for missing
`server_default` on new `NOT NULL` columns against a non-empty table, see
`migrations/versions/035daf1517e0_*.py` for a worked example).

**Keycloak/auth issues:** the realm/clients/reviewer user are provisioned
automatically (see §1) — check `docker compose logs keycloak-init` first;
it fails loudly (missing required `.env` variable) rather than silently
leaving a client without a secret. A `401`/`invalid_client_credentials`
after a `.env` secret change almost always means a service still holds
the old value in memory — `docker compose up -d --force-recreate backend
keycloak-init` to pick up the new one. A `401`/`invalid_grant` with no
further detail is Keycloak's intentional opaque response (never leaks
whether the email exists vs. the password was wrong).

## 6. Source changes

Freep's page structure is the pipeline's single point of fragility — see
[`../docs/DISCOVERY_REPORT.md`](../docs/DISCOVERY_REPORT.md) for the exact structure relied upon
(`__NUXT_DATA__` JSON payload, `span.rounded-full` contract-type badge,
`ul.mt-8 > li` info items, `h4` "De eisen"/"De wensen" headings). If Freep
changes its markup:

- **Discovery breaks first and loudest**: `CoverageChecker`'s displayed-
  count comparison will stop matching, the route falls to `partial`, and
  `scan_status` falls to `INCOMPLETE` — this is a deliberate fail-safe,
  not a bug, per AC02/AC03/AC11 (never silently claim complete coverage
  when it can't be demonstrated).
- **Parser field extraction breaks more quietly**: a renamed CSS class or
  restructured detail page can make `JobParser` return `None` for a field
  it used to extract, without raising an error. `tests/test_job_parser.py`
  runs against a fixed HTML fixture, not live Freep HTML, so it will
  *not* catch a live markup change — only a manual `scripts/validate.py
  <url>` run against a real page, or `quality.validation_errors`/
  `completeness_status` on freshly-scanned records, will surface this.
- **Fixing it**: update the relevant `_extract_*` method in
  `src/freep_pipeline/parsing/job_parser.py` (or `discovery/
  freep_discovery.py` for the `__NUXT_DATA__` shape), update
  `tests/test_job_parser.py`'s fixture to match the new real markup, and
  re-run the full suite before deploying.

## Known limitations (operational)

- **No automatic/recurring scheduler yet**: scans start manually — via
  the CLI (`scripts/scrape.py`) or the "Run scan now" button (§3) — but
  nothing triggers one on a recurring cadence (e.g. daily) without a human
  or an external cron acting. Concurrent runs *are* prevented (the
  advisory lock in §3), so wiring in cron (or an OS task scheduler) to
  call the trigger endpoint or the CLI on a schedule is safe to do without
  further code changes. See `SOLUTION_PROPOSAL.md` for options considered.
- **No push alerting**: a stale (`/health` "stale") or failed scan is only
  visible by polling — no email/Slack notification exists.
- **`AGREED_SCAN_FREQUENCY_HOURS` (24h) is a placeholder**, not yet
  formalized by Dreev (brief §9.1 "known limitations... operational
  choices").
- **LLM-assisted extraction (profile/engagement/procedure) depends on two
  external services (OpenAI primary, Groq fallback)** — no local fallback
  is wired in; if both are unreachable or rate-limited, these fields are
  simply left empty for that scan rather than blocking it (never a reason
  to fabricate — see `extraction/llm_field_extractor.py`).
- **AC13** (sample jointly validated against the live Freep source by
  Dreev) has not been done — needs a human review pass, not a technical
  fix.
