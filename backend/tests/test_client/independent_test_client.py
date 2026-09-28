"""AC15: an independent test client for the future matching tool.

Deliberately does NOT import anything from freep_pipeline — no ORM models,
no Pydantic schemas, no repository. It only knows: an HTTP base URL, a
Keycloak token endpoint, and plain JSON. This is the point of AC15 ("the
dataset can be read without manual conversion by a test client for the
future matching tool"): if this script needs to reach into the pipeline's
own code to make sense of the response, the API isn't actually
machine-readable on its own.

Usage:
    python tests/test_client/independent_test_client.py

Requires the API running (uvicorn src.freep_pipeline.api.main:app) and
Keycloak running with the dreev realm configured (see runbook), plus these
env vars (see .env.example): KEYCLOAK_ISSUER_URL, FREEP_TEST_CLIENT_ID,
FREEP_TEST_CLIENT_SECRET, API_BASE_URL.
"""

from __future__ import annotations

import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

KEYCLOAK_ISSUER_URL = os.environ.get("KEYCLOAK_ISSUER_URL", "http://localhost:8080/realms/dreev")
TEST_CLIENT_ID = os.environ.get("FREEP_TEST_CLIENT_ID", "freep-test-client")
TEST_CLIENT_SECRET = os.environ.get("FREEP_TEST_CLIENT_SECRET")
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


class IndependentTestClientError(Exception):
    pass


def get_access_token() -> str:
    """Machine-to-machine auth: client_credentials grant against Keycloak,
    same as any real automated matching-tool client would do."""
    if not TEST_CLIENT_SECRET:
        raise IndependentTestClientError(
            "FREEP_TEST_CLIENT_SECRET is not set — see .env.example for the required variables."
        )

    response = httpx.post(
        f"{KEYCLOAK_ISSUER_URL}/protocol/openid-connect/token",
        data={
            "grant_type": "client_credentials",
            "client_id": TEST_CLIENT_ID,
            "client_secret": TEST_CLIENT_SECRET,
        },
        timeout=10.0,
    )
    if response.status_code != 200:
        raise IndependentTestClientError(f"Token request failed: HTTP {response.status_code} {response.text}")
    return response.json()["access_token"]


def fetch_jobs(access_token: str) -> dict:
    response = httpx.get(
        f"{API_BASE_URL}/api/v1/jobs",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10.0,
    )
    if response.status_code != 200:
        raise IndependentTestClientError(f"GET /jobs failed: HTTP {response.status_code} {response.text}")
    return response.json()  # plain dict from response.json() — no manual conversion


def fetch_health() -> dict:
    response = httpx.get(f"{API_BASE_URL}/api/v1/health", timeout=10.0)
    if response.status_code != 200:
        raise IndependentTestClientError(f"GET /health failed: HTTP {response.status_code} {response.text}")
    return response.json()


def main() -> int:
    print(f"Requesting access token from {KEYCLOAK_ISSUER_URL} ...")
    token = get_access_token()
    print("Token acquired.\n")

    print("GET /api/v1/health")
    health = fetch_health()
    print(f"  status={health['status']} last_scan={health['last_successful_scan_id']}\n")

    print("GET /api/v1/jobs")
    payload = fetch_jobs(token)
    jobs = payload["items"]
    print(f"  {len(jobs)} job(s) returned\n")

    for job in jobs:
        # Every field read here comes straight from the JSON body — no
        # pipeline model, no schema import, just dict access. This is the
        # proof required by AC15.
        identity = job["identity"]
        core = job["core"]
        version = job["version"]
        print(
            f"  - {identity['internal_job_id']}: {core['title']!r} "
            f"(schema_version={job['schema_version']}, record_version={version['record_version']}, "
            f"change_type={job['change_type']})"
        )

    print("\nIndependent test client finished without any manual conversion or pipeline imports.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
