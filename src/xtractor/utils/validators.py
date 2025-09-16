from __future__ import annotations

from typing import Any, Iterable, Mapping

from xtractor.pipeline.state import DXField, DXSchema


class SchemaValidationError(ValueError):
    """Raised when the incoming schema payload is invalid."""


class PayloadValidationError(ValueError):
    """Raised when request payload cannot be parsed."""


def validate_output_format(value: str) -> str:
    target = value.lower().strip()
    if target != "json":
        raise PayloadValidationError("Only outputFormat='json' is supported")
    return "json"


def validate_field(field: Mapping[str, Any], index: int) -> DXField:
    name = field.get("name")
    if not name or not isinstance(name, str):
        raise SchemaValidationError(f"Field #{index + 1} is missing a valid 'name'")
    description = field.get("description")
    if description is not None and not isinstance(description, str):
        raise SchemaValidationError(
            f"Field '{name}' has invalid description type ({type(description).__name__})"
        )
    value = field.get("value")
    return DXField(name=name, description=description, value=value)


def validate_schema(schema: Mapping[str, Any]) -> DXSchema:
    key = schema.get("key")
    if not key or not isinstance(key, str):
        raise SchemaValidationError("Schema requires a non-empty 'key' string")
    raw_fields = schema.get("fields")
    if not isinstance(raw_fields, Iterable):
        raise SchemaValidationError("Schema 'fields' must be an iterable of field definitions")
    fields: list[DXField] = []
    for idx, field in enumerate(raw_fields):
        if not isinstance(field, Mapping):
            raise SchemaValidationError(f"Schema field at index {idx} is not an object")
        fields.append(validate_field(field, idx))
    if not fields:
        raise SchemaValidationError("Schema requires at least one field definition")
    return DXSchema(key=key, fields=fields)


def extract_schema_from_payload(payload: Mapping[str, Any]) -> DXSchema:
    schema = payload.get("schema")
    if not isinstance(schema, Mapping):
        raise PayloadValidationError("payload.schema must be an object")
    return validate_schema(schema)


def ensure_payload(payload: Mapping[str, Any]) -> tuple[str, DXSchema]:
    if "outputFormat" not in payload:
        raise PayloadValidationError("payload.outputFormat is required")
    output_format = validate_output_format(str(payload["outputFormat"]))
    schema = extract_schema_from_payload(payload)
    return output_format, schema


__all__ = [
    "PayloadValidationError",
    "SchemaValidationError",
    "ensure_payload",
    "extract_schema_from_payload",
    "validate_output_format",
    "validate_schema",
]
