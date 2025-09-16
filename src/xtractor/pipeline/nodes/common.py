from __future__ import annotations

from time import perf_counter
from typing import MutableMapping

from xtractor.pipeline.state import DXState


def start_timer() -> float:
    return perf_counter()


def record_latency(state: MutableMapping[str, object], node_name: str, start_time: float) -> None:
    elapsed_ms = int((perf_counter() - start_time) * 1000)
    metrics = state.setdefault("metrics", {})  # type: ignore[assignment]
    if isinstance(metrics, dict):
        timings = metrics.setdefault("timings_ms", {})  # type: ignore[assignment]
        if isinstance(timings, dict):
            timings[node_name] = elapsed_ms


__all__ = ["record_latency", "start_timer"]
