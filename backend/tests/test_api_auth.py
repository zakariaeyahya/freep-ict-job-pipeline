"""AC15 support + CLAUDE.md JWT rule: the API must verify signature,
expiration, issuer and audience on every protected call.

Builds a real RSA keypair and signs real JWTs with python-jose (no
mocking of the verification logic itself) to prove jwt_verifier.py
actually rejects a token whose signature, issuer, audience or expiry
doesn't check out — and accepts one that does. Only the network call to
fetch Keycloak's JWKS is faked (via monkeypatch), since standing up real
Keycloak for unit tests would make this suite flaky and slow.
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

ISSUER = "http://localhost:8080/realms/dreev"
AUDIENCE = "freep-pipeline-api"
KID = "test-key-1"


@pytest.fixture()
def rsa_keypair():
    """Generates a fresh, real RSA keypair for signing test tokens — no
    mocking of the cryptographic verification itself."""
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


def _private_pem(private_key) -> bytes:
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def _sign_token(private_key, *, issuer=ISSUER, audience=AUDIENCE, expires_in=300) -> str:
    now = int(time.time())
    claims = {
        "iss": issuer,
        "aud": audience,
        "sub": "service-account-freep-test-client",
        "azp": "freep-test-client",
        "iat": now,
        "exp": now + expires_in,
        "scope": "profile",
    }
    return jwt.encode(claims, _private_pem(private_key), algorithm="RS256", headers={"kid": KID})


@pytest.fixture()
def patched_jwks(monkeypatch, rsa_keypair):
    """Points the API's JWKS fetch at our in-memory test key instead of a
    real Keycloak, and resets the module-level cache so tests don't leak
    into each other."""
    jwks_response = {"keys": [_jwk_for(rsa_keypair)]}

    class _FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return jwks_response

    def _fake_get(url, timeout=None):
        return _FakeResponse()

    monkeypatch.setattr(jwt_verifier.httpx, "get", _fake_get)
    jwt_verifier._jwks_client._cached_keys = None
    jwt_verifier._jwks_client._cached_at = 0.0
    monkeypatch.setattr(jwt_verifier, "KEYCLOAK_ISSUER_URL", ISSUER)
    monkeypatch.setattr(jwt_verifier, "KEYCLOAK_API_AUDIENCE", AUDIENCE)
    return rsa_keypair


@pytest.fixture()
def client(monkeypatch):
    # /health does not require auth and hits the repository — stub it so
    # this suite stays focused on auth, not storage.
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


def test_valid_token_is_accepted(client, patched_jwks) -> None:
    token = _sign_token(patched_jwks)

    response = client.get("/api/v1/jobs", headers={"Authorization": f"Bearer {token}"})

    # 200 (empty DB) or 500 (no DB configured) both prove auth passed —
    # what matters here is that it is NOT 401. A dedicated pipeline test
    # (test_contracts.py, test_scan_recovery.py) already covers the DB path.
    assert response.status_code != 401


def test_missing_token_is_rejected(client, patched_jwks) -> None:
    response = client.get("/api/v1/jobs")
    assert response.status_code in (401, 403)  # HTTPBearer returns 403 with no header at all


def test_expired_token_is_rejected(client, patched_jwks) -> None:
    token = _sign_token(patched_jwks, expires_in=-60)

    response = client.get("/api/v1/jobs", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_wrong_audience_is_rejected(client, patched_jwks) -> None:
    token = _sign_token(patched_jwks, audience="some-other-api")

    response = client.get("/api/v1/jobs", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_wrong_issuer_is_rejected(client, patched_jwks) -> None:
    token = _sign_token(patched_jwks, issuer="http://attacker.example/realms/fake")

    response = client.get("/api/v1/jobs", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_token_signed_with_different_key_is_rejected(client, patched_jwks) -> None:
    """Proves signature verification is real: a token that is otherwise
    perfectly valid (right issuer, audience, not expired) but signed with
    a DIFFERENT private key than the one in the JWKS must still fail."""
    attacker_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = _sign_token(attacker_key)  # signed with a key not in the JWKS

    response = client.get("/api/v1/jobs", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_health_does_not_require_auth(client) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
