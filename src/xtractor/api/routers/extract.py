from __future__ import annotations

import json
from typing import Any, Dict, List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError

from xtractor.models.payload import ExtractPayload
from xtractor.models.responses import (
    AuditModel,
    ErrorResponse,
    ExtractResponse,
    ExtractionResultModel,
    SymbolLegendItemModel,
    SymbolSectionModel,
)
from xtractor.pipeline.runner import run_pipeline
from xtractor.pipeline.state import DXState
from xtractor.utils.validators import PayloadValidationError, SchemaValidationError

router = APIRouter(prefix="/v1", tags=["extract"])


def _parse_payload(payload_raw: str) -> Dict[str, Any]:
    try:
        payload_dict = json.loads(payload_raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(code="PAYLOAD_INVALID", message=str(exc)).model_dump(),
        ) from exc

    try:
        payload_model = ExtractPayload.model_validate(payload_dict)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(code="PAYLOAD_INVALID", message=json.dumps(exc.errors())).model_dump(),
        ) from exc
    return payload_model.model_dump(by_alias=True)


def _build_symbols_section(state: DXState) -> SymbolSectionModel:
    context = state.get("symbol_context") or {}
    legend_raw = context.get("legend") or []
    legend: List[SymbolLegendItemModel] = []
    for item in legend_raw:
        legend.append(
            SymbolLegendItemModel(
                symbol=item.get("symbol", ""),
                meaning=item.get("meaning", ""),
                pages=item.get("pages", []),
                bbox=item.get("bbox"),
            )
        )
    used = context.get("used") if isinstance(context, dict) else False
    return SymbolSectionModel(used=bool(used and legend), legend=legend)


def _build_audit_section(state: DXState) -> AuditModel:
    audit_raw = state.get("audit") or {}
    timings_raw = audit_raw.get("timings_ms") or {}
    timings = dict(timings_raw) if isinstance(timings_raw, dict) else {}
    latency = sum(timings.values()) if timings else None
    return AuditModel(
        graph_run_id=audit_raw.get("graph_run_id", ""),
        nodes_path=audit_raw.get("nodes_path", []),
        timings_ms=timings or None,
        latency_ms=latency,
    )


def _build_success_response(state: DXState) -> ExtractResponse:
    result = state.get("extraction_result") or {}
    extraction = ExtractionResultModel(
        key=result.get("key", ""),
        rows=result.get("rows", []),
    )
    summary = state.get("concise_summary") or ""
    warnings = state.get("warnings") or []
    symbols = _build_symbols_section(state)
    audit = _build_audit_section(state)
    return ExtractResponse(
        concise_summary=summary,
        result=extraction,
        symbols=symbols,
        audit=audit,
        warnings=list(warnings),
    )


@router.post(
    "/extract",
    response_model=ExtractResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    },
)
async def extract_endpoint(
    file: UploadFile = File(...),
    payload: str = Form(...),
) -> ExtractResponse:
    payload_dict = _parse_payload(payload)
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(code="FILE_INVALID", message="Uploaded file is empty").model_dump(),
        )

    try:
        state = run_pipeline(
            file_bytes=file_bytes,
            filename=file.filename or "upload.bin",
            payload=payload_dict,
        )
    except (PayloadValidationError, SchemaValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(code="SCHEMA_INVALID", message=str(exc)).model_dump(),
        ) from exc
    except Exception as exc:  # pragma: no cover - pipeline failure fallback
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(code="PIPELINE_FAILED", message=str(exc)).model_dump(),
        ) from exc

    return _build_success_response(state)


__all__ = ["router"]
