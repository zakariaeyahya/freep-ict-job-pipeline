"""POST /api/v1/scans/trigger: starts a scan on a background thread and
returns immediately (brief §9.2, Scheduler: "starts scheduled and manual
scans"). Uses a fake ScanTriggerService injected via FastAPI's dependency
override, consistent with how the rest of the API test suite avoids
hitting a real database/Keycloak for route-level behavior.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.freep_pipeline.api.main import app
from src.freep_pipeline.api.routes.scans import get_scan_trigger_service
from src.freep_pipeline.api.services.scan_trigger_service import ScanAlreadyRunningError

client = TestClient(app)


class _FakeTriggerService:
    def __init__(self, raises: Exception | None = None) -> None:
        self._raises = raises
        self.calls = 0

    def trigger_scan(self) -> None:
        self.calls += 1
        if self._raises:
            raise self._raises


def _with_fake_auth():
    """This suite only cares about trigger-service behavior, not JWT
    verification (already covered exhaustively in test_api_auth.py) — the
    verify_access_token dependency is overridden directly rather than
    signing a real token per test."""
    from src.freep_pipeline.api.auth.jwt_verifier import AuthenticatedPrincipal, verify_access_token

    app.dependency_overrides[verify_access_token] = lambda: AuthenticatedPrincipal(
        subject="test-user", client_id="test-client", scopes=[]
    )


def _clear_overrides():
    app.dependency_overrides.clear()


def test_trigger_starts_a_scan_and_returns_202() -> None:
    _with_fake_auth()
    fake_service = _FakeTriggerService()
    app.dependency_overrides[get_scan_trigger_service] = lambda: fake_service

    try:
        response = client.post("/api/v1/scans/trigger")
    finally:
        _clear_overrides()

    assert response.status_code == 202
    assert response.json() == {"status": "started"}
    assert fake_service.calls == 1


def test_trigger_returns_409_when_a_scan_is_already_running() -> None:
    _with_fake_auth()
    fake_service = _FakeTriggerService(raises=ScanAlreadyRunningError("A scan is already running"))
    app.dependency_overrides[get_scan_trigger_service] = lambda: fake_service

    try:
        response = client.post("/api/v1/scans/trigger")
    finally:
        _clear_overrides()

    assert response.status_code == 409
    body = response.json()
    assert body["error"] == "scan_already_running"


def test_trigger_requires_authentication() -> None:
    response = client.post("/api/v1/scans/trigger")

    assert response.status_code in (401, 403)
