"""GET /api/v1/scans/current: read-only view of the running scan's
progress, backing the Scan Report page's live "scan in progress" UI.
Uses FastAPI's dependency override, same pattern as test_scan_trigger.py.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.freep_pipeline.api.main import app
from src.freep_pipeline.api.routes.scans import get_scan_progress_service
from src.freep_pipeline.api.services.scan_progress import ScanProgressTracker

client = TestClient(app)


def _with_fake_auth():
    from src.freep_pipeline.api.auth.jwt_verifier import AuthenticatedPrincipal, verify_access_token

    app.dependency_overrides[verify_access_token] = lambda: AuthenticatedPrincipal(
        subject="test-user", client_id="test-client", scopes=[]
    )


def _clear_overrides():
    app.dependency_overrides.clear()


def test_returns_204_when_no_scan_is_running() -> None:
    _with_fake_auth()
    app.dependency_overrides[get_scan_progress_service] = lambda: ScanProgressTracker()

    try:
        response = client.get("/api/v1/scans/current")
    finally:
        _clear_overrides()

    assert response.status_code == 204
    assert response.content == b""


def test_returns_progress_when_a_scan_is_running() -> None:
    _with_fake_auth()
    tracker = ScanProgressTracker()
    tracker.start()
    tracker.report_discovery_finished(87)
    tracker.report_job_processed(54, 87, "Senior Mendix Developer")
    app.dependency_overrides[get_scan_progress_service] = lambda: tracker

    try:
        response = client.get("/api/v1/scans/current")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    body = response.json()
    assert body["phase"] == "processing"
    assert body["jobs_total"] == 87
    assert body["jobs_processed"] == 54
    assert len(body["activity"]) >= 1


def test_requires_authentication() -> None:
    response = client.get("/api/v1/scans/current")

    assert response.status_code in (401, 403)
