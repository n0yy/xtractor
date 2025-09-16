from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Iterable
from uuid import uuid4


ALLOWED_MIME_TYPES: set[str] = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def persist_temp_file(data: bytes, original_name: str | None, temp_dir: Path) -> Path:
    """Persist raw bytes into the configured temp directory."""

    suffix = Path(original_name or "uploaded").suffix
    handle = temp_dir / f"dx-{uuid4().hex}{suffix}"
    handle.write_bytes(data)
    return handle


def sniff_mime(path: Path, fallback: str | None = None) -> str:
    """Best-effort mime detection relying on file extension."""

    mime, _ = mimetypes.guess_type(path.name)
    if mime:
        return mime
    if fallback:
        return fallback
    return "application/octet-stream"


def ensure_allowed_mime(mime: str) -> None:
    if mime not in ALLOWED_MIME_TYPES:
        allowed = ", ".join(sorted(ALLOWED_MIME_TYPES))
        raise ValueError(f"Unsupported mime type '{mime}'. Allowed: {allowed}")


def read_chunks(path: Path, chunk_size: int = 1024 * 1024) -> Iterable[bytes]:
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            yield chunk


__all__ = [
    "ALLOWED_MIME_TYPES",
    "persist_temp_file",
    "sniff_mime",
    "ensure_allowed_mime",
    "read_chunks",
]
