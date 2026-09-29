"""GET /scans, GET /scans/{scan_id}, GET /scans/current, POST /scans/trigger
— routes only map request/response, per CLAUDE.md; all logic lives in
ScanService/ScanTriggerService/ScanProgressTracker."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response

from src.freep_pipeline.api.auth.jwt_verifier import AuthenticatedPrincipal, verify_access_token
from src.freep_pipeline.api.schemas import (
    ScanListResponse,
    ScanProgressResponse,
    ScanRunResponse,
    ScanTriggerResponse,
)
from src.freep_pipeline.api.services.scan_progress import ScanProgressTracker, get_scan_progress_tracker
from src.freep_pipeline.api.services.scan_service import ScanService
from src.freep_pipeline.api.services.scan_trigger_service import ScanTriggerService

router = APIRouter(prefix="/api/v1/scans", tags=["scans"])


def get_scan_service() -> ScanService:
    return ScanService()


def get_scan_trigger_service() -> ScanTriggerService:
    return ScanTriggerService()


@router.get("", response_model=ScanListResponse)
def list_scans(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _principal: AuthenticatedPrincipal = Depends(verify_access_token),
    service: ScanService = Depends(get_scan_service),
) -> ScanListResponse:
    scans = service.list_scans(limit=limit, offset=offset)
    return ScanListResponse(items=scans, limit=limit, offset=offset)


@router.post("/trigger", response_model=ScanTriggerResponse, status_code=status.HTTP_202_ACCEPTED)
def trigger_scan(
    _principal: AuthenticatedPrincipal = Depends(verify_access_token),
    service: ScanTriggerService = Depends(get_scan_trigger_service),
) -> ScanTriggerResponse:
    # Starts a scan on a background thread and returns immediately — a
    # scan can take minutes, far longer than an HTTP request should hold
    # open. ScanAlreadyRunningError propagates to the app-level exception
    # handler, which maps it to 409 (the caller did nothing wrong, they
    # just need to wait for the in-progress scan).
    service.trigger_scan()
    return ScanTriggerResponse(status="started")


def get_scan_progress_service() -> ScanProgressTracker:
    return get_scan_progress_tracker()


@router.get(
    "/current",
    response_model=ScanProgressResponse | None,
    responses={204: {"description": "No scan is currently running"}},
)
def get_current_scan_progress(
    _principal: AuthenticatedPrincipal = Depends(verify_access_token),
    tracker: ScanProgressTracker = Depends(get_scan_progress_service),
) -> ScanProgressResponse | Response:
    # 204 (not a JSON null) when idle — lets the frontend tell "no scan
    # running" apart from "a scan is running but has no activity yet"
    # without parsing a body.
    progress = tracker.current()
    if progress is None:
        return Response(status_code=204)
    return ScanProgressResponse(
        phase=progress.phase,
        jobs_total=progress.jobs_total,
        jobs_processed=progress.jobs_processed,
        activity=[{"message": e.message, "at": e.at} for e in progress.activity],
        started_at=progress.started_at,
    )


@router.get("/{scan_id}", response_model=ScanRunResponse)
def get_scan(
    scan_id: str,
    _principal: AuthenticatedPrincipal = Depends(verify_access_token),
    service: ScanService = Depends(get_scan_service),
) -> ScanRunResponse:
    # ScanNotFoundError propagates to the app-level exception handler,
    # which maps it to a 404 with the uniform error body.
    return service.get_scan(scan_id)
