from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, List

from langchain_core.messages import HumanMessage, SystemMessage

from xtractor.adapters.llm import MissingLLMProviderError, build_multimodal_model, invoke_json
from xtractor.config.settings import get_settings
from xtractor.pipeline.nodes.common import record_latency, start_timer
from xtractor.pipeline.state import DXState

SYSTEM_INSTRUCTIONS = (
    "You are a FILE UNDERSTANDING agent. Return strict JSON with keys: "
    "concise_summary (string) and hints (array of strings)."
    " Summaries must be 3-10 sentences. Mention tables/legends if visible."
    " Use null when uncertain."
)

HUMAN_INSTRUCTIONS = (
    "Read the attached document. Summarize key sections (1-5 sentences)."
    " Indicate whether tables or symbol legends exist and approximate pages"
    " (e.g., 'table around page 2'). Provide 3-5 salient asset identifiers when obvious."
    " Respond with JSON only."
)


def _load_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def _fallback_summary(path: Path) -> tuple[str, List[str]]:
    raw = path.read_bytes()
    if not raw:
        return ("Document appears empty; unable to summarize.", [])
    preview = raw.decode("utf-8", errors="ignore")
    preview = " ".join(preview.split())[:600]
    if not preview:
        return ("Unable to extract textual preview from document.", [])
    return (f"Heuristic summary: {preview}", [])


def file_understanding(state: DXState) -> DXState:
    start = start_timer()
    file_ref = state.get("file_ref")
    if not file_ref:
        raise ValueError("Pipeline state must include file_ref before file_understanding")

    document_path = Path(file_ref)
    settings = get_settings()
    warnings = list(state.get("warnings") or [])

    try:
        model = build_multimodal_model(settings)
        encoded = _load_base64(document_path)
        messages = [
            SystemMessage(content=SYSTEM_INSTRUCTIONS),
            HumanMessage(
                content=[
                    {"type": "text", "text": HUMAN_INSTRUCTIONS},
                    {
                        "type": "file",
                        "source_type": "base64",
                        "mime_type": state.get("mime", "application/pdf"),
                        "data": encoded,
                        "filename": document_path.name,
                    },
                ]
            ),
        ]
        result = invoke_json(
            model,
            messages,
            response_format={"type": "json_object"},
        )
        parsed = result.parsed
        concise_summary = str(parsed.get("concise_summary") or parsed.get("summary") or "").strip()
        hints = parsed.get("hints") or []
        if not concise_summary:
            raise ValueError("Model returned empty summary")
    except MissingLLMProviderError as exc:
        concise_summary, hints = _fallback_summary(document_path)
        warnings.append(str(exc))
    except Exception as exc:  # pragma: no cover - degrade gracefully
        concise_summary, hints = _fallback_summary(document_path)
        warnings.append(f"file_understanding fallback: {exc}")

    state["concise_summary"] = concise_summary
    if hints:
        state["hints"] = list(hints)
    state["warnings"] = warnings
    record_latency(state, "file_understanding", start)
    return state


__all__ = ["file_understanding"]
