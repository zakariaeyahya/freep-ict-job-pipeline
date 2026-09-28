"""AC15: "the dataset can be read without manual conversion by a test
client for the future matching tool."

Drives the exact same HTTP contract independent_test_client.py uses
(GET /api/v1/jobs and /health with a Bearer token, read via plain
response.json()) against the real FastAPI app through TestClient's
in-process transport, so this proof runs in the automated suite without a
live uvicorn process or a real Keycloak. independent_test_client.py itself
is the standalone script meant to be run against a live server + Keycloak
(see its module docstring); this test proves the same contract holds.
"""

from __future__ import annotations

import time

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from jose import jwk, jwt

from src.freep_pipeline.api.auth import jwt_verifier
from src.freep_pipeline.api.main import app
from src.freep_pipeline.api.services.health_service import HealthService
from src.freep_pipeline.api.services.job_service import JobService

ISSUER = "http://localhost:8080/realms/dreev"
AUDIENCE = "freep-pipeline-api"
KID = "test-key-1"

SAMPLE_JOB_RECORD = {
    "schema_version": "1.0",
    "identity": {
        "internal_job_id": "freep-99001",
        "source_job_id": "freep-99001",
        "canonical_url": "https://www.freep.nl/opdracht/99001",
        "source": "freep",
    },
    "core": {
        "title": "Cloud Engineer",
        "client_name": "Acme Consulting",
        "description_original": "Build and maintain cloud infrastructure.",
        "description_clean": None,
    },
    "publication": {
        "publication_datetime": None,
        "closing_datetime": None,
        "timezone": "Europe/Amsterdam",
        "status": "open",
    },
    "delivery": {
        "location": "Utrecht",
        "remote_policy": None,
        "hours_min": None,
        "hours_max": None,
        "start_date": None,
        "end_date": None,
        "extension_options": None,
    },
    "selection": {
        "hard_requirements": [{"text": "Minimaal 5 jaar ervaring met Java", "evidence_ref": None}],
        "wishes": [],
        "award_criteria": [],
        "competencies": [],
    },
    "profile": {"education": [], "experience": [], "skills": [], "methods": [], "certifications": [], "languages": []},
    "commercial": {"rate_min": None, "rate_max": None, "currency": "EUR", "vat_basis": None, "travel_cost_policy": None},
    "engagement": {
        "contract_type": None,
        "zzp_allowed": None,
        "screening": None,
        "vog": None,
        "nationality_constraints": None,
        "supplier_conditions": None,
    },
    "procedure": {"positions": None, "max_candidates": None, "interview_window": None, "submission_instructions": None},
    "quality": {
        "completeness_status": "complete_within_scan_window",
        "validation_errors": [],
        "source_evidence": [],
        "confidence_per_field": None,
    },
    "version": {
        "first_seen_at": "2026-09-27T10:00:00+00:00",
        "last_seen_at": "2026-09-27T10:00:00+00:00",
        "changed_at": None,
        "content_hash": "sha256:abc123",
        "record_version": 1,
        "observation_state": "active",
    },
    "attachments": [],
    "change_type": "new",
}


@pytest.fixture()
def rsa_keypair():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _jwk_for(private_key) -> dict:
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    jwk_dict = jwk.construct(public_pem, algorithm="RS256").to_dict()
    jwk_dict["kid"] = KID
    jwk_dict["use"] = "sig"
    return jwk_dict


def _sign_token(private_key) -> str:
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    now = int(time.time())
    claims = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": "service-account-freep-test-client",
        "azp": "freep-test-client",
        "iat": now,
        "exp": now + 300,
        "scope": "profile",
    }
    return jwt.encode(claims, private_pem, algorithm="RS256", headers={"kid": KID})


@pytest.fixture()
def api_client(monkeypatch, rsa_keypair):
    """Real FastAPI app, in-process, with JWKS/auth faked to a real signed
    token and the job/health services stubbed with fixed sample data —
    isolates this test to "does the client read the API correctly",
    independent of DB state (already covered by test_scan_recovery.py and
    test_contracts.py)."""
    jwks_response = {"keys": [_jwk_for(rsa_keypair)]}

    class _FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return jwks_response

    monkeypatch.setattr(jwt_verifier.httpx, "get", lambda url, timeout=None: _FakeResponse())
    jwt_verifier._jwks_client._cached_keys = None
    jwt_verifier._jwks_client._cached_at = 0.0
    monkeypatch.setattr(jwt_verifier, "KEYCLOAK_ISSUER_URL", ISSUER)
    monkeypatch.setattr(jwt_verifier, "KEYCLOAK_API_AUDIENCE", AUDIENCE)

    monkeypatch.setattr(
        JobService, "list_jobs", lambda self, status, change_type, limit, offset: [SAMPLE_JOB_RECORD]
    )
    monkeypatch.setattr(
        HealthService,
        "get_health",
        lambda self: {
            "status": "ok",
            "last_successful_scan_id": "scan_test",
            "last_successful_scan_ended_at": "2026-09-28T00:00:00+00:00",
            "seconds_since_last_successful_scan": 60.0,
        },
    )
    return TestClient(app)


def test_independent_client_reads_jobs_without_manual_conversion(api_client, rsa_keypair) -> None:
    """independent_test_client.fetch_jobs() calls httpx.get() against a
    real base URL, which needs a live server process. Here we drive the
    exact same HTTP contract (Bearer header, same path, plain
    response.json()) through TestClient's in-process transport instead, so
    this proof runs in the automated suite without spinning up uvicorn."""
    token = _sign_token(rsa_keypair)

    response = api_client.get("/api/v1/jobs", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, response.text
    payload = response.json()

    assert payload["items"][0]["identity"]["internal_job_id"] == "freep-99001"
    assert payload["items"][0]["schema_version"] == "1.0"
    assert payload["items"][0]["change_type"] == "new"


def test_independent_client_reads_health_without_manual_conversion(api_client) -> None:
    response = api_client.get("/api/v1/health")
    assert response.status_code == 200
    health = response.json()
    assert health["status"] == "ok"
    assert health["last_successful_scan_id"] == "scan_test"
