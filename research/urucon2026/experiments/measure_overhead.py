"""Measure trace size and headless verification throughput."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean, median

from common import ROOT
from game.trace_contract import canonical_json
from game.trace_verifier import verify_payload


def minimal_projection(payload: dict) -> dict:
    """Construct a deliberately minimal action-log comparison baseline."""

    games = []
    for game in payload["games"]:
        rounds = []
        for round_entry in game["rounds"]:
            rounds.append(
                {
                    "round": round_entry["round"],
                    "gameplay_settings_snapshot": round_entry[
                        "gameplay_settings_snapshot"
                    ],
                    "initial_state": round_entry["initial_state"],
                    "plays": [
                        {
                            "bot_id": play["bot_id"],
                            "cmd": play["normalized_command"],
                            "post_state": play["post_state"],
                        }
                        for play in round_entry["plays"]
                    ],
                }
            )
        games.append({"game_id": game["game_id"], "rounds": rounds})
    return {"games": games}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--corpus",
        default=str(ROOT / "research/urucon2026/corpus/generated"),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows: list[dict[str, object]] = []
    for path in sorted(Path(args.corpus).glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        report = verify_payload(payload)
        trace_bytes = len(canonical_json(payload).encode("utf-8"))
        baseline_bytes = len(
            canonical_json(minimal_projection(payload)).encode("utf-8")
        )
        plays = report.transitions
        rows.append(
            {
                "session": path.name,
                "privacy_mode": payload["privacy_mode"],
                "plays": plays,
                "trace_bytes": trace_bytes,
                "minimal_action_log_bytes": baseline_bytes,
                "bytes_per_play": f"{trace_bytes / plays:.3f}",
                "expansion_ratio": f"{trace_bytes / baseline_bytes:.6f}",
                "verification_ms": f"{report.elapsed_ms:.6f}",
                "plays_per_second": (
                    f"{plays / (report.elapsed_ms / 1000):.3f}"
                ),
            }
        )

    results_dir = ROOT / "research/urucon2026/results"
    results_dir.mkdir(parents=True, exist_ok=True)
    output = results_dir / "overhead.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "sessions": len(rows),
        "median_expansion_ratio_vs_minimal_action_log": median(
            float(row["expansion_ratio"]) for row in rows
        ),
        "mean_bytes_per_play": mean(
            float(row["bytes_per_play"]) for row in rows
        ),
        "median_verification_ms": median(
            float(row["verification_ms"]) for row in rows
        ),
        "median_plays_per_second": median(
            float(row["plays_per_second"]) for row in rows
        ),
    }
    (results_dir / "overhead-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
