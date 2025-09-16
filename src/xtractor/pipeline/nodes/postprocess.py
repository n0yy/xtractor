from __future__ import annotations

from collections import OrderedDict
from typing import Any, Dict, List
from uuid import uuid4

from xtractor.pipeline.nodes.common import record_latency, start_timer
from xtractor.pipeline.state import AuditInfo, DXField, DXSchema, DXState, ExtractionResult

NODE_SEQUENCE = [
    "file_understanding",
    "prompt_builder",
    "symbol_agent",
    "prompt_merge",
    "multimodal_extract",
    "postprocess",
]


def _normalize_row(schema_fields: List[DXField], row: Dict[str, Any], warnings: List[str]) -> Dict[str, Any]:
    normalized: "OrderedDict[str, Any]" = OrderedDict()
    for field in schema_fields:
        name = field["name"]
        value = row.get(name)
        if isinstance(value, str) and not value.strip():
            warnings.append(f"Empty string normalized to null for field '{name}'")
            value = None
        normalized[name] = value
    return dict(normalized)


def postprocess(state: DXState) -> DXState:
    start = start_timer()
    schema: DXSchema | None = state.get("schema")
    result: ExtractionResult | None = state.get("extraction_result")
    if not schema or not result:
        raise ValueError("multimodal_extract must populate schema and extraction result")

    warnings = list(state.get("warnings") or [])

    rows = result.get("rows") or []
    normalized_rows: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            warnings.append("Dropping non-object row from extraction result")
            continue
        normalized_rows.append(_normalize_row(schema["fields"], row, warnings))

    if not normalized_rows:
        normalized_rows.append(_normalize_row(schema["fields"], {}, warnings))

    cleaned_result = {"key": schema["key"], "rows": normalized_rows}
    metrics = dict(state.get("metrics") or {})
    timings_obj = metrics.get("timings_ms")
    timings = dict(timings_obj) if isinstance(timings_obj, dict) else {}
    audit: AuditInfo = {
        "graph_run_id": metrics.get("graph_run_id"),
        "nodes_path": NODE_SEQUENCE,
        "timings_ms": timings,
    }
    if not audit.get("graph_run_id"):
        audit["graph_run_id"] = f"run_{uuid4().hex[:12]}"

    state["extraction_result"] = cleaned_result
    state["warnings"] = warnings
    state["audit"] = audit
    state["metrics"] = metrics
    record_latency(state, "postprocess", start)
    return state


__all__ = ["postprocess"]
