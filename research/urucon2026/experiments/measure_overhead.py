"""Measure canonical trace size and repeated in-memory verification throughput."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
from pathlib import Path
from statistics import mean, median
from time import perf_counter

from common import ROOT
from game.trace_contract import canonical_json
from game.trace_verifier import verify_payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--corpus",
        default=str(ROOT / "research/urucon2026/corpus/generated"),
    )
    parser.add_argument("--repetitions", type=int, default=7)
    return parser


def _summary(rows: list[dict[str, object]]) -> dict[str, float | int]:
    return {
        "sessions": len(rows),
        "mean_raw_bytes_per_play": mean(
            float(row["raw_bytes_per_play"]) for row in rows
        ),
        "mean_gzip_bytes_per_play": mean(
            float(row["gzip_bytes_per_play"]) for row in rows
        ),
        "median_verification_ms": median(
            float(row["median_verification_ms"]) for row in rows
        ),
        "median_plays_per_second": median(
            float(row["plays_per_second"]) for row in rows
        ),
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.repetitions < 3:
        raise ValueError("At least three repetitions are required.")
    rows: list[dict[str, object]] = []
    for path in sorted(Path(args.corpus).glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        canonical = canonical_json(payload).encode("utf-8")
        compressed = gzip.compress(canonical, compresslevel=9, mtime=0)
        timings: list[float] = []
        report = verify_payload(payload)
        if not report.valid:
            raise RuntimeError(f"Cannot measure invalid trace: {path}")
        for _ in range(args.repetitions):
            started = perf_counter()
            report = verify_payload(payload)
            timings.append((perf_counter() - started) * 1000.0)
            if not report.valid:
                raise RuntimeError(f"Trace became invalid during measurement: {path}")
        plays = report.transitions
        elapsed = median(timings)
        rows.append(
            {
                "session": path.name,
                "privacy_mode": payload["privacy_mode"],
                "plays": plays,
                "raw_bytes": len(canonical),
                "gzip_bytes": len(compressed),
                "raw_bytes_per_play": f"{len(canonical) / plays:.3f}",
                "gzip_bytes_per_play": f"{len(compressed) / plays:.3f}",
                "median_verification_ms": f"{elapsed:.6f}",
                "plays_per_second": f"{plays / (elapsed / 1000.0):.3f}",
                "repetitions": args.repetitions,
                "timing_scope": "parsed-payload in-memory verification",
            }
        )

    if not rows:
        raise RuntimeError("No corpus traces were available for measurement.")
    results_dir = ROOT / "research/urucon2026/results"
    results_dir.mkdir(parents=True, exist_ok=True)
    output = results_dir / "overhead.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    modes = sorted({str(row["privacy_mode"]) for row in rows})
    summary = {
        "repetitions_per_session": args.repetitions,
        "timing_scope": "parsed-payload in-memory verification",
        "overall": _summary(rows),
        "by_privacy_mode": {
            mode: _summary([row for row in rows if row["privacy_mode"] == mode])
            for mode in modes
        },
    }
    (results_dir / "overhead-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
