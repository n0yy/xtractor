from __future__ import annotations

import re
from typing import Dict, List

from xtractor.config.settings import get_settings
from xtractor.pipeline.nodes.common import record_latency, start_timer
from xtractor.pipeline.state import DXState, SymbolContext, SymbolLegendItem

KNOWN_LEGENDS: Dict[str, str] = {
    "XV": "On/Off Valve",
    "CB": "Circuit Breaker",
    "TR": "Transformer",
    "PT": "Pressure Transmitter",
    "FT": "Flow Transmitter",
}
SYMBOL_RE = re.compile(r"\b[A-Z]{2,3}\b")


def symbol_agent(state: DXState) -> DXState:
    start = start_timer()
    settings = get_settings()
    summary = state.get("concise_summary") or ""
    matches = SYMBOL_RE.findall(summary)

    legend: List[SymbolLegendItem] = []
    for match in matches:
        meaning = KNOWN_LEGENDS.get(match)
        if not meaning:
            continue
        legend.append(SymbolLegendItem(symbol=match, meaning=meaning, pages=[]))

    context: SymbolContext = {"legend": legend}
    if legend:
        context["used"] = settings.enable_symbol_agent
    else:
        context.update({"used": False, "notes": "No symbol legend detected heuristically"})

    warnings = list(state.get("warnings") or [])
    if not legend:
        warnings.append("Symbol agent executed heuristic fallback; no legend detected")
    state["symbol_context"] = context
    state["warnings"] = warnings
    record_latency(state, "symbol_agent", start)
    return state


__all__ = ["symbol_agent", "KNOWN_LEGENDS"]
