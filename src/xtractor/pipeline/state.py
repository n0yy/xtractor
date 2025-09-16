from __future__ import annotations

from typing import Any, Dict, List, Literal, Mapping, MutableMapping, Optional
from typing_extensions import NotRequired, TypedDict


class DXField(TypedDict, total=False):
    name: str
    description: NotRequired[str]
    value: NotRequired[Any]


class DXSchema(TypedDict):
    key: str
    fields: List[DXField]


class DXError(TypedDict, total=False):
    code: str
    message: str
    where: NotRequired[str]


class SymbolLegendItem(TypedDict, total=False):
    symbol: str
    meaning: str
    pages: List[int]
    bbox: List[List[float]]


class SymbolContext(TypedDict, total=False):
    legend: List[SymbolLegendItem]
    used: NotRequired[bool]
    notes: NotRequired[str]


class ExtractionResult(TypedDict, total=False):
    key: str
    rows: List[Mapping[str, Any]]


class AuditInfo(TypedDict, total=False):
    graph_run_id: str
    nodes_path: List[str]
    timings_ms: Dict[str, int]


class DXState(TypedDict, total=False):
    """Shared LangGraph state for the pipeline."""

    # ingestion inputs
    file_bytes: bytes
    filename: str
    payload: Mapping[str, Any]

    # derived input data
    file_ref: str
    mime: str
    schema: DXSchema
    output_format: Literal["json"]

    # agent outputs
    concise_summary: str
    hints: List[str]
    system_prompt_draft: str
    symbol_context: Optional[SymbolContext]
    system_prompt_final: str
    extraction_result: ExtractionResult

    # pipeline metadata
    warnings: List[str]
    errors: List[DXError]
    metrics: Dict[str, Any]
    audit: AuditInfo


StateDict = MutableMapping[str, Any]


__all__ = [
    "AuditInfo",
    "DXError",
    "DXField",
    "DXSchema",
    "DXState",
    "ExtractionResult",
    "StateDict",
    "SymbolContext",
    "SymbolLegendItem",
]
