"""Verifies Keycloak-issued JWT access tokens for every protected endpoint.

Per CLAUDE.md (Backend - Python - Security & API): "If using JWT, verify
signature, expiration, issuer, and audience, and never put secrets in the
payload." All four checks happen here, and nowhere else — routes only ever
see the already-verified claims via FastAPI's dependency injection.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JOSEError

from config.logging_config import get_logger
from config.settings import KEYCLOAK_API_AUDIENCE, KEYCLOAK_ISSUER_URL, KEYCLOAK_JWKS_URL

logger = get_logger(__name__)

_JWKS_CACHE_TTL_SECONDS = 300

_bearer_scheme = HTTPBearer(auto_error=True)


@dataclass
class AuthenticatedPrincipal:
    """The verified identity of the caller, derived from token claims.
    Never carries the raw token — routes only need who is calling, not the
    credential itself."""

    subject: str
    client_id: str
    scopes: list[str]


class JwksClient:
    """Fetches and caches Keycloak's signing keys (JWKS). Keys are cached
    for a short TTL rather than forever, so a Keycloak key rotation is
    picked up without restarting the API."""

    def __init__(self, jwks_url: str = KEYCLOAK_JWKS_URL) -> None:
        self._jwks_url = jwks_url
        self._cached_keys: dict[str, Any] | None = None
        self._cached_at: float = 0.0

    def get_signing_key(self, kid: str) -> dict[str, Any]:
        keys = self._get_keys()
        key = next((k for k in keys if k.get("kid") == kid), None)
        if key is None:
            # The key may have rotated since our last fetch; refresh once
            # before giving up, rather than trusting a stale cache forever.
            keys = self._get_keys(force_refresh=True)
            key = next((k for k in keys if k.get("kid") == kid), None)
        if key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token signed with an unknown key",
            )
        return key

    def _get_keys(self, force_refresh: bool = False) -> list[dict[str, Any]]:
        now = time.monotonic()
        is_stale = (now - self._cached_at) > _JWKS_CACHE_TTL_SECONDS
        if self._cached_keys is None or is_stale or force_refresh:
            response = httpx.get(self._jwks_url, timeout=5.0)
            response.raise_for_status()
            self._cached_keys = response.json()["keys"]
            self._cached_at = now
        return self._cached_keys


_jwks_client = JwksClient()


def verify_access_token(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> AuthenticatedPrincipal:
    """FastAPI dependency: verifies signature, expiration, issuer and
    audience on every call. Raises 401 for any failure — a malformed,
    expired, mis-issued, or wrong-audience token is never distinguished in
    the response body, so callers cannot probe why a token was rejected."""
    token = credentials.credentials

    try:
        unverified_header = jwt.get_unverified_header(token)
    except JOSEError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed access token"
        ) from exc

    kid = unverified_header.get("kid")
    if not kid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed access token")

    signing_key = _jwks_client.get_signing_key(kid)

    try:
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=[signing_key.get("alg", "RS256")],
            audience=KEYCLOAK_API_AUDIENCE,
            issuer=KEYCLOAK_ISSUER_URL,
            options={"require_exp": True, "require_iat": True},
        )
    except JOSEError as exc:
        logger.warning("Token rejected: %s", exc)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token") from exc

    return AuthenticatedPrincipal(
        subject=claims["sub"],
        client_id=claims.get("azp", claims.get("client_id", "")),
        scopes=claims.get("scope", "").split(),
    )
