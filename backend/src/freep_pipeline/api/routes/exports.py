"""GET /exports/{scan_id}.jsonl — routes only map request/response, per
CLAUDE.md; all logic lives in ExportService.

Returns raw JSON Lines (one schema-validated JobRecord per line, UTF-8),
not a JSON array — brief §5.2's batch-matching/embeddings consumers expect
to stream and parse line-by-line, not load one large JSON document.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from src.freep_pipeline.api.auth.jwt_verifier import AuthenticatedPrincipal, verify_access_token
from src.freep_pipeline.api.services.export_service import ExportService

router = APIRouter(prefix="/api/v1/exports", tags=["exports"])


def get_export_service() -> ExportService:
    return ExportService()


@router.get("/{scan_id}.jsonl")
def export_scan_jsonl(
    scan_id: str,
    _principal: AuthenticatedPrincipal = Depends(verify_access_token),
    service: ExportService = Depends(get_export_service),
) -> Response:
    # ScanNotFoundError propagates to the app-level exception handler,
    # which maps it to a 404 with the uniform error body.
    records = service.export_scan_as_jsonl_lines(scan_id)
    body = "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
    if records:
        body += "\n"
    return Response(content=body, media_type="application/x-ndjson; charset=utf-8")
