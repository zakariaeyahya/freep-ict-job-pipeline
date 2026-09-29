"""CORS must be configured per allowed origin, never "*" (CLAUDE.md:
"Configure CORS per allowed origin, never `*`"), and the browser's
preflight OPTIONS request must succeed for the review UI's origin —
otherwise every cross-origin call (login included) fails before it
even reaches the route handler.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.freep_pipeline.api.main import app

client = TestClient(app)


def test_preflight_request_from_allowed_origin_succeeds() -> None:
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_preflight_request_from_disallowed_origin_is_not_granted_cors_headers() -> None:
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://evil.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    # Starlette's CORS middleware still returns 200 for the preflight
    # itself, but without an allow-origin header the browser blocks the
    # actual request — this is the real enforcement point.
    assert "access-control-allow-origin" not in response.headers


def test_cors_never_allows_wildcard_origin() -> None:
    from src.freep_pipeline.api.main import CORS_ALLOWED_ORIGINS

    assert "*" not in CORS_ALLOWED_ORIGINS
