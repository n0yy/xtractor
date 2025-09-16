"""Document Xtractor package."""

from importlib import metadata

try:  # pragma: no cover - best effort metadata lookup
    __version__ = metadata.version("xtractor")
except metadata.PackageNotFoundError:  # pragma: no cover - local dev fallback
    __version__ = "0.0.0"

__all__ = ["__version__"]
