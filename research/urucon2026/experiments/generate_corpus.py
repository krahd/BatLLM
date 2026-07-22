"""Generate and verify the controlled-command evaluation corpus."""

from __future__ import annotations

import argparse
import csv
from copy import deepcopy
import json
from pathlib import Path

from common import ROOT, initial_state, repository_commit
from game.replay_engine import GameplaySettingsSnapshot
from game.research_runtime import (
    InvocationPolicy,
    MediatedGameRuntime,
    ScriptedClient,
)
from game.session_v3 import write_session_v3
from game.trace_contract import (
    PrivacyMode,
    finalise_play_hash,
    sha256_json,
)
from game.trace_verifier import verify_payload

COMMANDS = ["M", "M0.05", "C15", "A30", "S", "S1", "S0", "B", "nonsense"]
_STABLE_TIME = "2026-01-01T00:00:00+00:00"


def stabilise_fixture_metadata(payload: dict, index: int) -> dict:
    """Remove incidental UUID/timing variance from the reference corpus.

    Environment provenance is retained. IDs, wall-clock timestamps, and model
    latency are not semantic inputs, so deterministic fixture values make
    corpus hashes and storage measurements repeatable on the same environment.
    """

    result = deepcopy(payload)
    result["session_id"] = f"session_{index:03d}"
    result["created_at"] = _STABLE_TIME
    previous: str | None = None
    sequence = 0
    for game_index, game in enumerate(result["games"], start=1):
        game["game_id"] = game_index
        game["started_at"] = _STABLE_TIME
        for round_index, round_entry in enumerate(game["rounds"], start=1):
            round_entry["round"] = round_index
            round_entry["started_at"] = _STABLE_TIME
            round_entry["ended_at"] = _STABLE_TIME
            updated_plays = []
            for play in round_entry["plays"]:
                sequence += 1
                play["play_id"] = f"play_{index:03d}_{sequence:03d}"
                play["sequence"] = sequence
                play["request_started_at"] = _STABLE_TIME
                play["request_completed_at"] = _STABLE_TIME
                play["latency_ms"] = 0.0
                updated = finalise_play_hash(play, previous)
                previous = updated["play_sha256"]
                updated_plays.append(updated)
            round_entry["plays"] = updated_plays
    result.pop("session_sha256", None)
    result["session_sha256"] = sha256_json(result)
    return result


def build_session(
    index: int, plays: int, privacy: PrivacyMode, git_commit: str | None
) -> dict[str, object]:
    rules = GameplaySettingsSnapshot.from_mapping(
        {
            "bot_diameter": 0.08 + 0.01 * (index % 3),
            "bot_step_length": 0.02 + 0.01 * (index % 4),
            "bullet_damage": 3 + (index % 5),
            "bullet_diameter": 0.02,
            "bullet_step_length": 0.01,
            "shield_size": 45 + 5 * (index % 6),
            "shield_initial_state": False,
            "initial_health": 30,
            "turns_per_round": plays,
            "total_rounds": 1,
        }
    )
    sequence = [COMMANDS[(index + offset) % len(COMMANDS)] for offset in range(plays)]
    runtime = MediatedGameRuntime(
        client=ScriptedClient(sequence),
        initial_state=initial_state(0.005 * (index % 4)),
        rules=rules,
        policy=InvocationPolicy(
            provider="scripted",
            model=f"fixture-{index % 4}",
            options={"temperature": 0, "seed": index},
        ),
        system_instructions=(
            "Return exactly one command from the BatLLM grammar."
        ),
        prompt_augmentation=bool(index % 2),
        independent_contexts=bool((index // 2) % 2),
        privacy_mode=privacy,
        git_commit=git_commit,
        model_provenance={
            "fixture_family": "scripted",
            "fixture_index": index,
        },
    )
    runtime.start_round(
        {1: "Choose a tactical action.", 2: "Choose a defensive action."}
    )
    completed = 0
    turn = 0
    while completed < plays:
        prompts = {
            1: f"Tactical turn {turn}.",
            2: f"Defensive turn {turn}.",
        }
        for bot_id in (1, 2):
            if completed >= plays:
                break
            runtime.play(bot_id=bot_id, human_prompt=prompts[bot_id])
            completed += 1
        turn += 1
    return stabilise_fixture_metadata(runtime.session_payload(), index)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sessions", type=int, default=60)
    parser.add_argument("--plays", type=int, default=18)
    parser.add_argument(
        "--output",
        default=str(ROOT / "research/urucon2026/corpus/generated"),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    for stale in output_dir.glob("session-*.json"):
        stale.unlink()

    rows: list[dict[str, object]] = []
    modes = list(PrivacyMode)
    git_commit = repository_commit()
    for index in range(args.sessions):
        payload = build_session(
            index, args.plays, modes[index % len(modes)], git_commit
        )
        path = write_session_v3(
            payload, output_dir / f"session-{index:03d}.json"
        )
        report = verify_payload(payload)
        rows.append(
            {
                "session": path.name,
                "privacy_mode": payload["privacy_mode"],
                "plays": report.transitions,
                "valid": report.valid,
                "exact_requests": report.exact_requests,
                "redacted_requests": report.redacted_requests,
                "commitment_only_requests": report.commitment_only_requests,
                "verified_groundings": report.verified_groundings,
                "commitment_only_groundings": report.commitment_only_groundings,
                "state_equivalent_plays": report.state_equivalent_transitions,
                "event_equivalent_plays": report.event_equivalent_transitions,
                "verification_ms": f"{report.elapsed_ms:.6f}",
                "bytes": path.stat().st_size,
            }
        )

    results_dir = ROOT / "research/urucon2026/results"
    results_dir.mkdir(parents=True, exist_ok=True)
    results_path = results_dir / "replay-fidelity.csv"
    with results_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "sessions": len(rows),
        "plays": sum(int(row["plays"]) for row in rows),
        "valid_sessions": sum(bool(row["valid"]) for row in rows),
        "exact_requests": sum(int(row["exact_requests"]) for row in rows),
        "redacted_requests": sum(int(row["redacted_requests"]) for row in rows),
        "commitment_only_requests": sum(
            int(row["commitment_only_requests"]) for row in rows
        ),
        "verified_groundings": sum(
            int(row["verified_groundings"]) for row in rows
        ),
        "commitment_only_groundings": sum(
            int(row["commitment_only_groundings"]) for row in rows
        ),
        "state_equivalent_plays": sum(
            int(row["state_equivalent_plays"]) for row in rows
        ),
        "event_equivalent_plays": sum(
            int(row["event_equivalent_plays"]) for row in rows
        ),
        "privacy_modes": {
            mode.value: sum(row["privacy_mode"] == mode.value for row in rows)
            for mode in modes
        },
        "source_revision": git_commit,
        "stable_fixture_metadata": True,
    }
    (results_dir / "replay-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))
    complete = (
        summary["valid_sessions"] == summary["sessions"]
        and summary["state_equivalent_plays"] == summary["plays"]
        and summary["event_equivalent_plays"] == summary["plays"]
    )
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
