from __future__ import annotations

from xtractor.pipeline.nodes.common import record_latency, start_timer
from xtractor.pipeline.state import DXState, SymbolContext


def _render_symbol_section(context: SymbolContext | None) -> str:
    if not context:
        return "[SYMBOL LEGEND]\nNone provided."
    legend = context.get("legend") or []
    if not legend:
        note = context.get("notes") or "Symbol agent reported no legend."
        return f"[SYMBOL LEGEND]\n{note}"
    lines = []
    for entry in legend:
        symbol = entry.get("symbol", "?")
        meaning = entry.get("meaning", "")
        pages = ", ".join(str(p) for p in entry.get("pages") or []) or "n/a"
        lines.append(f"{symbol} = {meaning} (pages: {pages})")
    return "[SYMBOL LEGEND]\n" + "\n".join(lines)


def prompt_merge(state: DXState) -> DXState:
    start = start_timer()
    draft = state.get("system_prompt_draft")
    if not draft:
        raise ValueError("Prompt builder must run before prompt_merge")
    symbol_section = _render_symbol_section(state.get("symbol_context"))
    final_prompt = draft + "\n\n" + symbol_section
    state["system_prompt_final"] = final_prompt
    record_latency(state, "prompt_merge", start)
    return state


__all__ = ["prompt_merge"]
