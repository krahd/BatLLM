"""Inject controlled semantic faults and re-anchor ordinary trace commitments."""

from __future__ import annotations

import argparse
import csv
from copy import deepcopy
import json
from pathlib import Path
from typing import Callable

from common import ROOT
from game.replay_engine import parse_model_response
from game.trace_contract import (
    PrivacyMode,
    finalise_play_hash,
    sha256_json,
    sha256_text,
    transition_hash,
)
from game.trace_verifier import verify_payload

Payload = dict[str, object]
Mutator = Callable[[Payload], None]
Applicability = Callable[[Payload], bool]


def _first_play(payload: Payload) -> dict:
    return payload["games"][0]["rounds"][0]["plays"][0]  # type: ignore[index]


def _round(payload: Payload) -> dict:
    return payload["games"][0]["rounds"][0]  # type: ignore[index]


def _different_command(current: str) -> str:
    for candidate in ("M0.2", "C90", "B", "S1", "nonsense"):
        parsed = parse_model_response(candidate)
        if parsed.normalized_cmd != current:
            return candidate
    raise AssertionError("No alternative command fixture available.")


def alter_command(payload: Payload) -> None:
    play = _first_play(payload)
    play["normalized_command"] = parse_model_response(
        _different_command(play["normalized_command"])
    ).normalized_cmd


def alter_response(payload: Payload) -> None:
    play = _first_play(payload)
    play["response"]["text"] = _different_command(  # type: ignore[index]
        play["normalized_command"]
    )


def alter_request(payload: Payload) -> None:
    request = _first_play(payload)["request"]
    request["payload"]["model"] = "tampered-model"  # type: ignore[index]


def alter_human_prompt(payload: Payload) -> None:
    _first_play(payload)["human_prompt"]["text"] = "tampered prompt"  # type: ignore[index]


def alter_supplied_state(payload: Payload) -> None:
    state = _first_play(payload)["game_state_supplied_to_model"]["bots"]  # type: ignore[index]
    first_key = next(iter(state))
    state[first_key]["x"] = 0.99


def alter_rules(payload: Payload) -> None:
    _round(payload)["gameplay_settings_snapshot"]["bot_diameter"] = 0.9  # type: ignore[index]


def alter_pre_state(payload: Payload) -> None:
    state = _first_play(payload)["pre_state"]
    first_key = next(iter(state))
    state[first_key]["x"] = 0.99


def alter_post_state(payload: Payload) -> None:
    state = _first_play(payload)["post_state"]
    first_key = next(iter(state))
    state[first_key]["health"] = 1


def alter_events(payload: Payload) -> None:
    _first_play(payload)["events"] = []


def delete_play(payload: Payload) -> None:
    _round(payload)["plays"].pop(0)  # type: ignore[index]


def reorder_plays(payload: Payload) -> None:
    plays = _round(payload)["plays"]
    plays[:2] = reversed(plays[:2])  # type: ignore[index]


def _all(_payload: Payload) -> bool:
    return True


def _full(payload: Payload) -> bool:
    return payload["privacy_mode"] == PrivacyMode.FULL.value


def _retained_request(payload: Payload) -> bool:
    return payload["privacy_mode"] != PrivacyMode.HASHED.value


FAULTS: dict[str, tuple[Mutator, Applicability]] = {
    "alter-command": (alter_command, _all),
    "alter-response": (alter_response, _full),
    "alter-request": (alter_request, _retained_request),
    "alter-human-prompt": (alter_human_prompt, _full),
    "alter-supplied-state": (alter_supplied_state, _all),
    "alter-rules": (alter_rules, _all),
    "alter-pre-state": (alter_pre_state, _all),
    "alter-post-state": (alter_post_state, _all),
    "alter-events": (alter_events, _all),
    "delete-play": (delete_play, _all),
    "reorder-plays": (reorder_plays, _all),
}


def _reanchor_protected_text(record: object) -> None:
    if not isinstance(record, dict):
        return
    text = record.get("text")
    if text is None or text == "[REDACTED]":
        return
    rendered = str(text)
    record["sha256"] = sha256_text(rendered)
    record["length"] = len(rendered)


def _reanchor_request(request: dict) -> None:
    payload = request.get("payload")
    if not isinstance(payload, dict):
        return
    request["stored_sha256"] = sha256_json(payload)
    if request.get("privacy_mode") == PrivacyMode.FULL.value:
        request["canonical_sha256"] = sha256_json(payload)


def reanchor_trace(payload: Payload) -> None:
    """Recompute every commitment derivable from retained mutated content.

    The procedure deliberately cannot reconstruct original text hidden by
    redacted or hash-only modes. Such mutations are excluded by applicability.
    """

    previous: str | None = None
    for game in payload["games"]:  # type: ignore[index]
        for round_entry in game["rounds"]:
            rules = round_entry["gameplay_settings_snapshot"]
            for prompt in round_entry.get("prompts", []):
                _reanchor_protected_text(prompt.get("prompt"))
            reanchored = []
            for play in round_entry["plays"]:
                _reanchor_protected_text(play.get("human_prompt"))
                _reanchor_protected_text(play.get("system_instructions"))
                _reanchor_protected_text(play.get("response"))
                error = play.get("error")
                if isinstance(error, dict):
                    _reanchor_protected_text(error.get("message"))
                _reanchor_request(play["request"])
                play["transition_sha256"] = transition_hash(
                    bot_id=play["bot_id"],
                    pre_state=play["pre_state"],
                    command=play["normalized_command"],
                    rules=rules,
                    post_state=play["post_state"],
                    events=play["events"],
                )
                updated = finalise_play_hash(play, previous)
                previous = updated["play_sha256"]
                reanchored.append(updated)
            round_entry["plays"] = reanchored
    material = deepcopy(payload)
    material.pop("session_sha256", None)
    payload["session_sha256"] = sha256_json(material)


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
    rows: list[dict[str, object]] = []
    for path in files:
        base = json.loads(path.read_text(encoding="utf-8"))
        for name, (mutate, applicable) in FAULTS.items():
            if not applicable(base):
                continue
            payload = deepcopy(base)
            mutate(payload)
            reanchor_trace(payload)
            report = verify_payload(payload)
            rows.append(
                {
                    "session": path.name,
                    "privacy_mode": base["privacy_mode"],
                    "fault": name,
                    "detected": not report.valid,
                    "issue_codes": "|".join(
                        sorted({issue.code for issue in report.issues})
                    ),
                }
            )

    if not rows:
        raise RuntimeError("No corpus traces were available for fault injection.")
    results_dir = ROOT / "research/urucon2026/results"
    results_dir.mkdir(parents=True, exist_ok=True)
    output = results_dir / "fault-detection.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    detected = sum(bool(row["detected"]) for row in rows)
    summary = {
        "sessions": len(files),
        "fault_classes": len(FAULTS),
        "applicable_faults": len(rows),
        "detected": detected,
        "detection_rate": detected / len(rows),
    }
    (results_dir / "fault-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))
    return 0 if detected == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
