from __future__ import annotations

from typing import Any, List, Literal

from pydantic import BaseModel, ConfigDict, Field


class SchemaFieldModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str | None = None
    value: Any | None = None


class SchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    fields: List[SchemaFieldModel]


class ExtractPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    output_format: Literal["json"] = Field(alias="outputFormat", default="json")
    schema: SchemaModel


__all__ = ["SchemaFieldModel", "SchemaModel", "ExtractPayload"]
