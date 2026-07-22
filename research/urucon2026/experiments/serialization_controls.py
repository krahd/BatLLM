"""Verify that benign JSON serialisation changes do not create false failures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import ROOT
from game.trace_verifier import verify_payload


def _reverse_keys(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _reverse_keys(value[key])
            for key in reversed(list(value.keys()))
        }
    if isinstance(value, list):
        return [_reverse_keys(item) for item in value]
    return value


def _variants(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "compact-ascii": json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=False,
            separators=(",", ":"),
        ),
        "pretty-unicode": json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=False,
            indent=4,
        )
        + "\n",
        "reversed-keys": json.dumps(
            _reverse_keys(payload),
            ensure_ascii=False,
            sort_keys=False,
            separators=(", ", ": "),
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--corpus",
        default=str(ROOT / "research/urucon2026/corpus/generated"),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    files = sorted(Path(args.corpus).glob("*.json"))
    accepted = 0
    variants = 0
    failures: list[dict[str, str]] = []
    by_variant: dict[str, dict[str, int]] = {}
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for name, rendered in _variants(payload).items():
            variants += 1
            parsed = json.loads(rendered)
            report = verify_payload(parsed)
            by_variant.setdefault(name, {"tested": 0, "accepted": 0})
            by_variant[name]["tested"] += 1
            if report.valid:
                accepted += 1
                by_variant[name]["accepted"] += 1
            else:
                failures.append(
                    {
                        "session": path.name,
                        "variant": name,
                        "issues": "|".join(issue.code for issue in report.issues),
                    }
                )
    summary = {
        "sessions": len(files),
        "variants": variants,
        "accepted": accepted,
        "false_rejections": variants - accepted,
        "by_variant": by_variant,
        "failures": failures[:20],
    }
    output = ROOT / "research/urucon2026/results/serialization-summary.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0 if accepted == variants else 1


if __name__ == "__main__":
    raise SystemExit(main())
