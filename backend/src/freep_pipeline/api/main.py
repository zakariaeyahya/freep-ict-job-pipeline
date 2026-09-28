"""FastAPI app entry point. Publishes the pipeline's job data as the
machine-readable interface AC15's independent test client reads
(brief §5, §9.2 "Publisher — Provides an API... with schema version").

Run with: uvicorn src.freep_pipeline.api.main:app --reload
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.freep_pipeline.api.routes import health, jobs
from src.freep_pipeline.api.services.job_service import JobNotFoundError

app = FastAPI(title="Freep ICT Job Pipeline API", version="1.0")

app.include_router(jobs.router)
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


@app.exception_handler(JobNotFoundError)
def handle_job_not_found(request: Request, exc: JobNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content=_error_body(request, 404, "job_not_found", str(exc)),
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
