"""GET /jobs, GET /jobs/{internal_job_id}, GET /jobs/{internal_job_id}/versions
— routes only map request/response, per CLAUDE.md; all logic lives in
JobService."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from src.freep_pipeline.api.auth.jwt_verifier import AuthenticatedPrincipal, verify_access_token
from src.freep_pipeline.api.schemas import JobListResponse, JobRecordResponse, JobVersionsResponse
from src.freep_pipeline.api.services.job_service import JobService

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


def get_job_service() -> JobService:
    return JobService()


@router.get("", response_model=JobListResponse)
def list_jobs(
    status: str | None = Query(default=None, description="Filter by job status (open, closed, unknown)"),
    change_type: str | None = Query(default=None, description="Filter by change_type"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _principal: AuthenticatedPrincipal = Depends(verify_access_token),
    service: JobService = Depends(get_job_service),
) -> JobListResponse:
    records = service.list_jobs(status=status, change_type=change_type, limit=limit, offset=offset)
    return JobListResponse(items=records, limit=limit, offset=offset)


@router.get("/{internal_job_id}", response_model=JobRecordResponse)
def get_job(
    internal_job_id: str,
    _principal: AuthenticatedPrincipal = Depends(verify_access_token),
    service: JobService = Depends(get_job_service),
) -> JobRecordResponse:
    # JobNotFoundError propagates to the app-level exception handler,
    # which maps it to a 404 with the uniform error body.
    return service.get_job(internal_job_id)


@router.get("/{internal_job_id}/versions", response_model=JobVersionsResponse)
def get_job_versions(
    internal_job_id: str,
    _principal: AuthenticatedPrincipal = Depends(verify_access_token),
    service: JobService = Depends(get_job_service),
) -> JobVersionsResponse:
    # JobNotFoundError (no observation at all for this id) propagates to
    # the app-level exception handler -> 404.
    return JobVersionsResponse(items=service.get_versions(internal_job_id))
