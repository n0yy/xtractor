from __future__ import annotations

from xtractor.pipeline.nodes.common import record_latency, start_timer
from xtractor.pipeline.state import DXState

SYMBOL_KEYWORDS = {"symbol", "legend", "p&id", "instrument", "loop", "isa"}


def symbol_router(state: DXState) -> str:
    start = start_timer()
    draft = (state.get("system_prompt_draft") or "").lower()
    summary = (state.get("concise_summary") or "").lower()
    combined = f"{draft}\n{summary}"
    decision = "symbol_needed" if any(keyword in combined for keyword in SYMBOL_KEYWORDS) else "skip"
    record_latency(state, "symbol_router", start)
    metrics = state.get("metrics") or {}
    metrics = dict(metrics)
    metrics["symbol_keywords_detected"] = decision == "symbol_needed"
    state["metrics"] = metrics
    return decision


__all__ = ["symbol_router", "SYMBOL_KEYWORDS"]
