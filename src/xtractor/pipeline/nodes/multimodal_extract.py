from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from xtractor.adapters.llm import MissingLLMProviderError, build_multimodal_model, invoke_json
from xtractor.config.settings import get_settings
from xtractor.pipeline.nodes.common import record_latency, start_timer
from xtractor.pipeline.state import DXField, DXState, ExtractionResult

PROMPT_SUFFIX = (
    "Use the attached document to populate rows. Respond in JSON with keys {key, rows}."
    " Each row must include every schema field; use null when not found."
)


def _load_document(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def _fallback_rows(fields: List[DXField]) -> List[Dict[str, Any]]:
    row: Dict[str, Any] = {}
    for field in fields:
        value = field.get("value")
        row[field["name"]] = value if value is not None else None
    return [row]


def multimodal_extract(state: DXState) -> DXState:
    start = start_timer()
    schema = state.get("schema")
    final_prompt = state.get("system_prompt_final")
    if not schema or not final_prompt:
        raise ValueError("prompt_merge must populate system_prompt_final and schema")

    file_ref = state.get("file_ref")
    if not file_ref:
        raise ValueError("file reference missing before multimodal_extract")

    doc_path = Path(file_ref)
    warnings = list(state.get("warnings") or [])
    settings = get_settings()

    try:
        model = build_multimodal_model(settings)
        encoded = _load_document(doc_path)
        messages = [
            SystemMessage(content=final_prompt),
            HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": PROMPT_SUFFIX,
                    },
                    {
                        "type": "file",
                        "source_type": "base64",
                        "mime_type": state.get("mime", "application/pdf"),
                        "data": encoded,
                        "filename": doc_path.name,
                    },
                ]
            ),
        ]
        response = invoke_json(
            model,
            messages,
            response_format={"type": "json_object"},
        )
        parsed = response.parsed
        rows = parsed.get("rows")
        if not isinstance(rows, list):
            raise ValueError("Model returned invalid rows payload")
        result: ExtractionResult = {
            "key": parsed.get("key") or schema["key"],
            "rows": rows,
        }
    except MissingLLMProviderError as exc:
        warnings.append(str(exc))
        result = {"key": schema["key"], "rows": _fallback_rows(schema["fields"])}
    except Exception as exc:  # pragma: no cover - degrade gracefully
        warnings.append(f"multimodal_extract fallback: {exc}")
        result = {"key": schema["key"], "rows": _fallback_rows(schema["fields"])}

    state["extraction_result"] = result
    state["warnings"] = warnings
    record_latency(state, "multimodal_extract", start)
    return state


__all__ = ["multimodal_extract"]
