# Freep ICT Job Data Pipeline

Discovers, retrieves, structures and validates ICT job assignments
published on [Freep](https://www.freep.nl), and delivers the resulting
dataset through a versioned API and export — Phase 1 of Dreev's broader
AI matching process (see
[`Dreev_Freep_Data_Pipeline_Workflow_EN.md`](Dreev_Freep_Data_Pipeline_Workflow_EN.md)
for the full brief).

Live deployment: [ict.bet](https://ict.bet) (review UI) ·
[api.ict.bet](https://api.ict.bet/api/v1/health) (API) ·
[auth.ict.bet](https://auth.ict.bet) (Keycloak admin console)

## Read this first

**[`docs/Dreev_Freep_Data_Pipeline_Report_EN.pdf`](docs/Dreev_Freep_Data_Pipeline_Report_EN.pdf)**
is the single document that summarizes context, methodology, architecture,
results and acceptance-criteria status — including the sample of real
scanned assignments prepared for Dreev's AC13 review. Start there.

## Repository layout

```text
backend/                  Python scan pipeline + FastAPI (see backend/README.md)
freep-ict-job-pipeline/   Next.js review UI (see its own README.md)
docker/                   Keycloak realm/init script, Caddy reverse proxy config
docker-compose.yml        Full stack: PostgreSQL, Keycloak, backend, frontend, Caddy
docs/                     Report (PDF + source), discovery report, deployment guide, diagrams
```

## Documentation index

| Document | Covers |
| --- | --- |
| [`docs/Dreev_Freep_Data_Pipeline_Report_EN.pdf`](docs/Dreev_Freep_Data_Pipeline_Report_EN.pdf) | Context, methodology, architecture, results, acceptance criteria, AC13 sample |
| [`docs/DISCOVERY_REPORT.md`](docs/DISCOVERY_REPORT.md) | Source analysis, robots.txt/terms-of-use review, open legal questions |
| [`backend/SOLUTION_PROPOSAL.md`](backend/SOLUTION_PROPOSAL.md) | Scan-worker architecture options and decision |
| [`backend/RUNBOOK.md`](backend/RUNBOOK.md) | Installation, configuration, monitoring, recovery, source-change playbook |
| [`backend/README.md`](backend/README.md) | Backend structure, API surface, auth setup, LLM extraction |
| [`freep-ict-job-pipeline/README.md`](freep-ict-job-pipeline/README.md) | Review UI setup |
| [`docs/HOSTINGER_DEPLOY.md`](docs/HOSTINGER_DEPLOY.md) | GitHub Actions → Hostinger VPS deployment |

## Running the full stack locally

```bash
cp .env.example .env   # fill in secrets — see comments in the file
docker compose up -d --build
```

No manual Keycloak setup is needed: the `dreev` realm and its three OAuth
clients import automatically from
[`docker/keycloak/dreev-realm.json`](docker/keycloak/dreev-realm.json) on
first startup, and `keycloak-init` pushes the secrets from `.env` into
that realm once. See `backend/README.md` → "Auth (Keycloak)" for details.

- Frontend: <http://localhost:3000>
- API: <http://localhost:8000>
- Keycloak admin console: <http://localhost:8080>

## Production deployment

Pushing to `main` runs backend/frontend tests, builds and publishes
Docker images, then deploys to the Hostinger VPS over SSH — see
[`docs/HOSTINGER_DEPLOY.md`](docs/HOSTINGER_DEPLOY.md) for the required
GitHub secrets/variables and the one-time VPS setup. Caddy terminates
HTTPS for all three domains with automatically renewed Let's Encrypt
certificates.

## Key design decisions

- **LLM extraction**: OpenAI primary, Groq automatic fallback. Best-effort
  only — a scan never blocks if both are unavailable (see
  `backend/src/freep_pipeline/extraction/`).
- **Never fabricate content**: every LLM-derived field value is verified
  to be an exact substring of the source text before being trusted.
- **Coverage checking**: each scan compares the number of discovered ICT
  jobs against Freep's own displayed count; a scan is marked
  `COMPLETE_WITHIN_SCAN_WINDOW` only when coverage is confirmed, all known
  routes succeeded, and every discovered job was processed without error.
