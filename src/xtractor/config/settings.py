from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field
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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""

    settings = Settings()
    settings.temp_dir.mkdir(parents=True, exist_ok=True)
    return settings


__all__ = ["Settings", "get_settings"]
