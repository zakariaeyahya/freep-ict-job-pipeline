"""FastAPI app entry point. Publishes the pipeline's job data as the
machine-readable interface AC15's independent test client reads
(brief §5, §9.2 "Publisher — Provides an API... with schema version").

Run with: uvicorn src.freep_pipeline.api.main:app --reload
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import CORS_ALLOWED_ORIGINS
from src.freep_pipeline.api.routes import auth, exports, health, jobs, scans
from src.freep_pipeline.api.services.auth_service import InvalidCredentialsError
from src.freep_pipeline.api.services.job_service import JobNotFoundError
from src.freep_pipeline.api.services.scan_service import ScanNotFoundError
from src.freep_pipeline.api.services.scan_trigger_service import ScanAlreadyRunningError

app = FastAPI(title="Freep ICT Job Pipeline API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(scans.router)
app.include_router(exports.router)
app.include_router(health.router)


def _error_body(request: Request, status_code: int, error: str, message: str) -> dict:
    # CLAUDE.md: uniform error body (timestamp, status, error code,
    # message, path), never a raw stack trace or internal class name.
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status_code,
        "error": error,
        "message": message,
        "path": request.url.path,
    }


@app.exception_handler(InvalidCredentialsError)
def handle_invalid_credentials(request: Request, exc: InvalidCredentialsError) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content=_error_body(request, 401, "invalid_credentials", str(exc)),
    )


@app.exception_handler(JobNotFoundError)
def handle_job_not_found(request: Request, exc: JobNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content=_error_body(request, 404, "job_not_found", str(exc)),
    )


@app.exception_handler(ScanNotFoundError)
def handle_scan_not_found(request: Request, exc: ScanNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content=_error_body(request, 404, "scan_not_found", str(exc)),
    )


@app.exception_handler(ScanAlreadyRunningError)
def handle_scan_already_running(request: Request, exc: ScanAlreadyRunningError) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content=_error_body(request, 409, "scan_already_running", str(exc)),
    )


@app.exception_handler(ValueError)
def handle_data_integrity_error(request: Request, exc: ValueError) -> JSONResponse:
    # A stored record failing its own published schema (JobService) is a
    # server-side data integrity fault, not something the caller can fix —
    # CLAUDE.md: 500 only for real unexpected server failures.
    return JSONResponse(
        status_code=500,
        content=_error_body(request, 500, "data_integrity_error", "The requested data failed internal validation."),
    )
