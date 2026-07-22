"""Validate every generated trace against the published JSON Schema."""

from __future__ import annotations

from copy import deepcopy
import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from common import ROOT


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--corpus",
        default=str(ROOT / "research/urucon2026/corpus/generated"),
    )
    parser.add_argument(
        "--schema",
        default=str(
            ROOT
            / "research/urucon2026/schema/batllm-session-v3.schema.json"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    schema = json.loads(Path(args.schema).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    files = sorted(Path(args.corpus).glob("*.json"))
    failures: list[dict[str, object]] = []
    valid = 0
    first_payload: dict | None = None
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        first_payload = first_payload or payload
        errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
        if errors:
            failures.append(
                {
                    "session": path.name,
                    "errors": [
                        {
                            "path": "/".join(str(part) for part in error.path),
                            "message": error.message,
                        }
                        for error in errors[:20]
                    ],
                }
            )
        else:
            valid += 1

    malformed_rejected = False
    if first_payload is not None:
        malformed = deepcopy(first_payload)
        malformed.pop("session_id", None)
        malformed_rejected = bool(list(validator.iter_errors(malformed)))

    summary = {
        "draft": "2020-12",
        "schema_valid": True,
        "sessions": len(files),
        "valid_sessions": valid,
        "invalid_sessions": len(files) - valid,
        "malformed_control_rejected": malformed_rejected,
        "failures": failures,
    }
    output = ROOT / "research/urucon2026/results/schema-summary.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))
    return 0 if valid == len(files) and malformed_rejected else 1


if __name__ == "__main__":
    raise SystemExit(main())
