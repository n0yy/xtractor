from __future__ import annotations

from pathlib import Path
from typing import Mapping
from uuid import uuid4

from xtractor.adapters.io import ensure_allowed_mime, persist_temp_file, sniff_mime
from xtractor.config.settings import get_settings
from xtractor.pipeline import compile_graph
from xtractor.pipeline.state import DXState
from xtractor.utils.validators import (
    PayloadValidationError,
    SchemaValidationError,
    ensure_payload,
)

_COMPILED_GRAPH = None


def _graph():
    global _COMPILED_GRAPH
    if _COMPILED_GRAPH is None:
        _COMPILED_GRAPH = compile_graph()
    return _COMPILED_GRAPH


def run_pipeline(*, file_bytes: bytes, filename: str, payload: Mapping[str, object]) -> DXState:
    state: DXState = {
        "file_bytes": bytes(file_bytes),
        "filename": filename,
        "payload": payload,
        "metrics": {"graph_run_id": f"thread_{uuid4().hex[:8]}"},
    }
    _prepare_ingress(state)
    graph = _graph()
    result: DXState = graph.invoke(state)
    return result


def _prepare_ingress(state: DXState) -> None:
    settings = get_settings()
    payload = state.get("payload")
    if payload is None:
        raise PayloadValidationError("State missing request payload for pipeline execution")

    try:
        output_format, schema = ensure_payload(payload)
    except (SchemaValidationError, PayloadValidationError):
        raise

    file_bytes = state.get("file_bytes")
    if not isinstance(file_bytes, (bytes, bytearray)):
        raise PayloadValidationError("State missing file_bytes for pipeline execution")

    filename = state.get("filename") or "uploaded.bin"
    temp_path = persist_temp_file(bytes(file_bytes), str(filename), settings.temp_dir)
    mime = sniff_mime(Path(temp_path))
    try:
        ensure_allowed_mime(mime)
    except ValueError as exc:
        raise PayloadValidationError(str(exc)) from exc

    metrics = dict(state.get("metrics") or {})
    metrics.update({
        "file_size_bytes": len(file_bytes),
        "filename": str(filename),
    })

    state.update(
        {
            "file_ref": str(temp_path),
            "mime": mime,
            "schema": schema,
            "output_format": output_format,
            "warnings": list(state.get("warnings") or []),
            "errors": list(state.get("errors") or []),
            "metrics": metrics,
        }
    )


__all__ = ["run_pipeline"]
