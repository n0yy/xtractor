from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI


from xtractor.config.settings import Settings, get_settings

from dotenv import load_dotenv

load_dotenv()

class JSONChatModel(Protocol):
    """Protocol implemented by LangChain chat models we rely on."""

    def invoke(self, messages: Sequence[BaseMessage | Mapping[str, Any] | str], **kwargs: Any) -> Any: ...


@dataclass
class ModelInvocationResult:
    raw: Any
    parsed: Mapping[str, Any]


class MissingLLMProviderError(RuntimeError):
    """Raised when required multimodal provider packages are missing."""


def build_multimodal_model(settings: Settings | None = None) -> JSONChatModel:
    """Instantiate the default multimodal model based on configuration."""

    settings = settings or get_settings()

    client = ChatOpenAI(
        model=settings.mm_model,
        temperature=0,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        extra_body={
            "reasoning": {
                "effort": "low"  # bisa 'low', 'medium', atau 'high'
            }
        }
    )
    return client

def invoke_json(
    model: JSONChatModel,
    messages: Sequence[BaseMessage | Mapping[str, Any] | str],
    response_format: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> ModelInvocationResult:
    """Invoke a chat model expecting JSON output and parse the response."""

    invocation_kwargs = dict(kwargs)
    if response_format:
        invocation_kwargs.setdefault("response_format", response_format)
    raw = model.invoke(messages, **invocation_kwargs)

    if hasattr(raw, "content"):
        payload = raw.content  # type: ignore[assignment]
    else:
        payload = raw

    if isinstance(payload, str):
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive branch
            raise ValueError(f"Model returned invalid JSON: {payload}") from exc
    elif isinstance(payload, Mapping):
        parsed = payload  # already JSON-like
    else:  # pragma: no cover - defensive branch
        raise TypeError(f"Unsupported model response type: {type(payload)}")

    return ModelInvocationResult(raw=raw, parsed=parsed)


__all__ = [
    "JSONChatModel",
    "ModelInvocationResult",
    "MissingLLMProviderError",
    "build_multimodal_model",
    "invoke_json",
]
