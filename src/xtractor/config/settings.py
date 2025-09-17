from __future__ import annotations

import json

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the extraction service."""

    model_config = SettingsConfigDict(
        env_prefix="DX_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["local", "dev", "prod"] = Field(default="local")
    mm_model: str = Field(default="gpt-4o-mini", description="Identifier for multimodal LLM")
    allowed_cors: list[str] = Field(
        default=["*"],
        description="Origins allowed to perform CORS requests",
    )
    summary_max_tokens: int = Field(default=600, ge=50, description="Upper bound for summary tokens")
    enable_symbol_agent: bool = Field(default=True, description="Toggle symbol agent execution")
    temp_dir: Path = Field(default=Path("./.tmp"), description="Workspace for temporary files")
    log_level: str = Field(default="INFO", description="Root log level")
    openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DX_OPENAI_API_KEY", "OPENAI_API_KEY"),
    )
    openai_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DX_OPENAI_BASE_URL", "OPENAI_BASE_URL"),
        description="Optional custom base URL for OpenAI-compatible endpoints (e.g., LiteLLM)",
    )

    @field_validator("allowed_cors", mode="before")
    def _deserialize_allowed_cors(cls, value: object) -> object:  # noqa: D401, N805
        """Accept JSON arrays or comma-delimited strings for CORS origins."""

        if not isinstance(value, str):
            return value

        stripped = value.strip().strip("'")
        if not stripped:
            return []

        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return [item.strip() for item in stripped.split(",") if item.strip()]

        if isinstance(parsed, str):
            return [parsed.strip()]
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]

        raise TypeError("allowed_cors must be a list of origins or a single origin string")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""

    settings = Settings()
    settings.temp_dir.mkdir(parents=True, exist_ok=True)
    return settings

__all__ = ["Settings", "get_settings"]
