"""POST /api/v1/auth/login — deliberately unauthenticated (that's the
point: this is how a caller GETS a token). Rate-limiting this endpoint is
listed as a follow-up (see CLAUDE.md Backend-Python-Security: "rate-limit
public and auth endpoints"), not yet wired in."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.freep_pipeline.api.schemas import LoginRequest, LoginResponse
from src.freep_pipeline.api.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def get_auth_service() -> AuthService:
    return AuthService()


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, service: AuthService = Depends(get_auth_service)) -> LoginResponse:
    # InvalidCredentialsError propagates to the app-level exception
    # handler, which maps it to a 401 with the uniform error body.
    return service.login(body.email, body.password)
