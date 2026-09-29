"""Business logic for POST /api/v1/auth/login. Routes call this; it never
talks HTTP directly (CLAUDE.md: "Never put business logic in FastAPI route
handlers. Routes call services, services hold the logic.").

The API never stores or checks a password itself — every credential is
forwarded to Keycloak via the Resource Owner Password Credentials (ROPC)
grant, and Keycloak's response (or rejection) is the only source of truth
for whether the login succeeds.
"""

from __future__ import annotations

import httpx

from config.logging_config import get_logger
from config.settings import (
    KEYCLOAK_REVIEWER_CLIENT_ID,
    KEYCLOAK_REVIEWER_CLIENT_SECRET,
    KEYCLOAK_TOKEN_URL,
)

logger = get_logger(__name__)


class InvalidCredentialsError(Exception):
    """Raised when Keycloak rejects the email/password pair. Deliberately
    carries no detail from Keycloak's response — never leak whether the
    email exists vs. the password was wrong (CLAUDE.md: never leak
    internals to the client)."""


class AuthService:
    def __init__(self, token_url: str = KEYCLOAK_TOKEN_URL, timeout_seconds: float = 10.0) -> None:
        self._token_url = token_url
        self._timeout_seconds = timeout_seconds

    def login(self, email: str, password: str) -> dict:
        try:
            response = httpx.post(
                self._token_url,
                data={
                    "grant_type": "password",
                    "client_id": KEYCLOAK_REVIEWER_CLIENT_ID,
                    "client_secret": KEYCLOAK_REVIEWER_CLIENT_SECRET,
                    "username": email,
                    "password": password,
                    "scope": "openid",
                },
                timeout=self._timeout_seconds,
            )
        except httpx.RequestError as exc:
            logger.error("Keycloak token endpoint unreachable: %s", exc)
            raise InvalidCredentialsError("Authentication service unavailable") from exc

        if response.status_code != 200:
            # Keycloak returns 401 for bad credentials, 400 for a disabled
            # user/realm misconfiguration — both are "login failed" from
            # the caller's point of view, nothing more specific is leaked.
            logger.warning("Keycloak login rejected (status=%s)", response.status_code)
            raise InvalidCredentialsError("Incorrect email or password")

        payload = response.json()
        return {
            "access_token": payload["access_token"],
            "expires_in": payload["expires_in"],
            "refresh_token": payload.get("refresh_token"),
            "refresh_expires_in": payload.get("refresh_expires_in"),
        }
