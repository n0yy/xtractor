from __future__ import annotations

import argparse
import json
from pathlib import Path

from pydantic import ValidationError

from xtractor.models.payload import ExtractPayload
from xtractor.models.responses import ExtractResponse
from xtractor.pipeline.runner import run_pipeline
from xtractor.pipeline.state import DXState


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Document Xtractor pipeline")
    parser.add_argument("file", type=Path, help="Path to PDF/DOCX input file")
    parser.add_argument("schema", type=Path, help="Path to schema JSON payload")
    parser.add_argument("--output", type=Path, help="Where to store JSON result")
    return parser.parse_args()


def _load_payload(path: Path) -> dict:
    raw = json.loads(path.read_text())
    try:
        payload = ExtractPayload.model_validate(raw)
    except ValidationError as exc:
        raise SystemExit(f"Invalid payload schema: {exc}") from exc
    return payload.model_dump(by_alias=True)


def _format_response(state: DXState) -> ExtractResponse:
    from xtractor.api.routers.extract import _build_success_response  # lazy import to reuse logic

    return _build_success_response(state)


def main() -> None:
    args = parse_args()
    if not args.file.exists():
        raise SystemExit(f"Input file not found: {args.file}")
    payload = _load_payload(args.schema)
    file_bytes = args.file.read_bytes()
    state = run_pipeline(file_bytes=file_bytes, filename=args.file.name, payload=payload)
    response = _format_response(state)
    output_json = response.model_dump_json(indent=2)

    if args.output:
        args.output.write_text(output_json)
    else:
        print(output_json)


if __name__ == "__main__":  # pragma: no cover
    main()
