"""GET /health — deliberately unauthenticated: a monitoring probe should
not need a token to check whether the pipeline is alive (brief §5.1, §6.3
"Freshness")."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.freep_pipeline.api.schemas import HealthResponse
from src.freep_pipeline.api.services.health_service import HealthService

router = APIRouter(prefix="/api/v1", tags=["health"])


def get_health_service() -> HealthService:
    return HealthService()


@router.get("/health", response_model=HealthResponse)
def get_health(service: HealthService = Depends(get_health_service)) -> HealthResponse:
    return service.get_health()
