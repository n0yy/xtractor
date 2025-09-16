from __future__ import annotations

import json
from typing import List

from xtractor.pipeline.nodes.common import record_latency, start_timer
from xtractor.pipeline.state import DXField, DXSchema, DXState

HEADER = "You are an Extraction Model. Output JSON ONLY with keys: {key, rows}."
FORMAT_RULES = (
    "- Keep field order per input schema.\n"
    "- Obey field names exactly.\n"
    "- Use null when information is missing or ambiguous.\n"
    "- Preserve units; split into components only when schema expects it."
)


def _format_field(field: DXField) -> str:
    description = field.get("description") or ""
    example = field.get("value")
    pieces: List[str] = [f"{field['name']}: {description}".strip()]
    if example is not None:
        pieces.append(f"example: {example}")
    return " (".join(pieces) + (")" if example is not None else "")


def _render_schema(schema: DXSchema) -> str:
    field_lines = "\n".join(f"- {_format_field(field)}" for field in schema["fields"])
    return f"key: {schema['key']}\nfields:\n{field_lines}"


def _render_example(schema: DXSchema) -> str | None:
    fields = schema.get("fields", [])
    example_row = {}
    has_value = False
    for field in fields:
        value = field.get("value")
        if value not in (None, ""):
            has_value = True
        example_row[field["name"]] = value if value not in (None, "") else None
    if not has_value:
        return None
    payload = {"key": schema["key"], "rows": [example_row]}
    return json.dumps(payload, ensure_ascii=False, indent=2)


def prompt_builder(state: DXState) -> DXState:
    start = start_timer()
    schema = state.get("schema")
    if not schema:
        raise ValueError("Schema must be present before prompt_builder runs")
    summary = state.get("concise_summary") or "Summary unavailable."
    hints = state.get("hints")
    schema_block = _render_schema(schema)
    example_block = _render_example(schema)

    prompt_sections = [
        HEADER,
        "\n[SCHEMA]\n" + schema_block,
        "\n[FILE SUMMARY]\n" + summary,
    ]
    if hints:
        hint_block = "\n".join(f"- {hint}" for hint in hints)
        prompt_sections.append("\n[HINTS]\n" + hint_block)
    if example_block:
        prompt_sections.append("\n[EXAMPLE OUTPUT]\n" + example_block)
    prompt_sections.append("\n[FORMAT RULES]\n" + FORMAT_RULES)

    draft = "\n".join(prompt_sections).strip()
    state["system_prompt_draft"] = draft
    if example_block:
        state["fewshot_example"] = example_block
    record_latency(state, "prompt_builder", start)
    return state


__all__ = ["prompt_builder"]
