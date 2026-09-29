"""POST /api/v1/auth/login: the API never checks a password itself — it
forwards email/password to Keycloak's token endpoint (ROPC grant) and
relays success/failure. Mocks httpx.post so no real Keycloak call happens
in this suite (real Keycloak + ROPC is exercised manually, see README).
"""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from src.freep_pipeline.api.main import app

client = TestClient(app)


class _FakeKeycloakResponse:
    def __init__(self, status_code: int, payload: dict) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict:
        return self._payload


def test_valid_credentials_return_an_access_token() -> None:
    keycloak_payload = {
        "access_token": "eyJ...fake",
        "expires_in": 300,
        "refresh_token": "refresh-fake",
        "refresh_expires_in": 1800,
    }

    with patch(
        "src.freep_pipeline.api.services.auth_service.httpx.post",
        return_value=_FakeKeycloakResponse(200, keycloak_payload),
    ):
        response = client.post("/api/v1/auth/login", json={"email": "reviewer@dreev.local", "password": "correct"})

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"] == "eyJ...fake"
    assert body["expires_in"] == 300
    assert body["refresh_token"] == "refresh-fake"


def test_wrong_password_returns_401_with_uniform_error_body() -> None:
    with patch(
        "src.freep_pipeline.api.services.auth_service.httpx.post",
        return_value=_FakeKeycloakResponse(401, {"error": "invalid_grant"}),
    ):
        response = client.post("/api/v1/auth/login", json={"email": "reviewer@dreev.local", "password": "wrong"})

    assert response.status_code == 401
    body = response.json()
    assert body["error"] == "invalid_credentials"
    assert "timestamp" in body and "path" in body
    # Never leak Keycloak's own error detail (e.g. "invalid_grant") to the
    # client — CLAUDE.md: never leak internals.
    assert "invalid_grant" not in body["message"]


def test_keycloak_unreachable_returns_401_not_a_500() -> None:
    """A down Keycloak is still an auth failure from the caller's point of
    view, not an unexpected server error — CLAUDE.md: 500 only for real
    unexpected server failures."""
    import httpx

    with patch(
        "src.freep_pipeline.api.services.auth_service.httpx.post",
        side_effect=httpx.ConnectError("connection refused"),
    ):
        response = client.post("/api/v1/auth/login", json={"email": "reviewer@dreev.local", "password": "any"})

    assert response.status_code == 401


def test_missing_email_or_password_is_rejected_by_request_validation() -> None:
    response = client.post("/api/v1/auth/login", json={"email": "reviewer@dreev.local"})

    assert response.status_code == 422


def test_login_does_not_require_a_bearer_token() -> None:
    """The login endpoint must itself be reachable without already having
    a token — otherwise nobody could ever log in."""
    with patch(
        "src.freep_pipeline.api.services.auth_service.httpx.post",
        return_value=_FakeKeycloakResponse(401, {"error": "invalid_grant"}),
    ):
        response = client.post("/api/v1/auth/login", json={"email": "x@x.com", "password": "x"})

    # No Authorization header was sent, yet the request reached the
    # handler (401 from Keycloak rejection, not 401/403 from missing auth).
    assert response.status_code == 401
