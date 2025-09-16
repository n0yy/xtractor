from __future__ import annotations

from typing import Any, Dict, List, Literal

from pydantic import BaseModel, ConfigDict, Field


class ExtractionRowModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    # dynamic fields per schema


class ExtractionResultModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    rows: List[Dict[str, Any]]


class SymbolLegendItemModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    meaning: str
    pages: List[int] = Field(default_factory=list)
    bbox: List[List[float]] | None = None


class SymbolSectionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    used: bool = False
    legend: List[SymbolLegendItemModel] = Field(default_factory=list)


class AuditModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    graph_run_id: str
    nodes_path: List[str]
    latency_ms: int | None = None
    timings_ms: Dict[str, int] | None = None


class ExtractResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"] = "ok"
    concise_summary: str
    result: ExtractionResultModel
    symbols: SymbolSectionModel
    audit: AuditModel
    warnings: List[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["error"] = "error"
    code: str
    message: str


__all__ = [
    "AuditModel",
    "ErrorResponse",
    "ExtractResponse",
    "ExtractionResultModel",
    "SymbolLegendItemModel",
    "SymbolSectionModel",
]
