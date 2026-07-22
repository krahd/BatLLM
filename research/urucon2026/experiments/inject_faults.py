"""Inject controlled semantic faults and re-anchor ordinary trace commitments.

Play-local perturbations are exercised at early, middle, and late positions of
each session. The round-level rules perturbation is applied once per session.
All hashes that can be recomputed from retained mutated content are re-anchored
before verification, so detection cannot be attributed to stale digests alone.
"""

from __future__ import annotations

import argparse
import csv
from copy import deepcopy
import json
from pathlib import Path
from typing import Callable

from common import ROOT
from game.replay_engine import (
    GameplaySettingsSnapshot,
    apply_play,
    compare_state_maps,
    parse_model_response,
)
from game.trace_contract import (
    PrivacyMode,
    canonical_json,
    event_to_dict,
    finalise_play_hash,
    sha256_json,
    sha256_text,
    transition_hash,
)
from game.trace_verifier import verify_payload

Payload = dict[str, object]
Mutator = Callable[[Payload, int], None]
Applicability = Callable[[Payload], bool]


def _round(payload: Payload) -> dict:
    return payload["games"][0]["rounds"][0]  # type: ignore[index]


def _plays(payload: Payload) -> list[dict]:
    return _round(payload)["plays"]


def _play(payload: Payload, index: int) -> dict:
    return _plays(payload)[index]


def _positions(payload: Payload) -> list[tuple[str, int]]:
    count = len(_plays(payload))
    candidates = (("early", 0), ("middle", count // 2), ("late", max(0, count - 2)))
    seen: set[int] = set()
    result: list[tuple[str, int]] = []
    for label, index in candidates:
        if index not in seen:
            result.append((label, index))
            seen.add(index)
    return result


def _different_command(current: str) -> str:
    for candidate in ("M0.2", "C90", "A45", "B", "S1", "S0", "nonsense"):
        parsed = parse_model_response(candidate)
        if parsed.normalized_cmd != current:
            return candidate
    raise AssertionError("No alternative command fixture available.")


def alter_command(payload: Payload, index: int) -> None:
    """Select a command guaranteed to alter replayed state or semantic events."""

    play = _play(payload, index)
    rules = GameplaySettingsSnapshot.from_mapping(
        _round(payload)["gameplay_settings_snapshot"]
    )
    for candidate in ("M0.2", "C90", "A45", "B", "S1", "S0", "nonsense"):
        parsed = parse_model_response(candidate)
        if parsed.normalized_cmd == play["normalized_command"]:
            continue
        resolution = apply_play(
            play["pre_state"],
            bot_id=play["bot_id"],
            llm_response=parsed.normalized_cmd,
            cmd_text=parsed.normalized_cmd,
            rules=rules,
        )
        replay_events = [event_to_dict(event) for event in resolution.events]
        state_same, _details = compare_state_maps(
            resolution.state_by_bot, play["post_state"]
        )
        events_same = canonical_json(replay_events) == canonical_json(play["events"])
        if not state_same or not events_same:
            play["normalized_command"] = parsed.normalized_cmd
            return
    raise RuntimeError("No semantically distinct command fixture available.")


def alter_response(payload: Payload, index: int) -> None:
    play = _play(payload, index)
    play["response"]["text"] = _different_command(play["normalized_command"])


def alter_request(payload: Payload, index: int) -> None:
    _play(payload, index)["request"]["payload"]["model"] = "tampered-model"


def alter_human_prompt(payload: Payload, index: int) -> None:
    _play(payload, index)["human_prompt"]["text"] = "tampered prompt"


def alter_supplied_state(payload: Payload, index: int) -> None:
    state = _play(payload, index)["game_state_supplied_to_model"]["bots"]
    first_key = next(iter(state))
    state[first_key]["x"] = 0.987654321


def alter_rules(payload: Payload, _index: int) -> None:
    snapshot = _round(payload)["gameplay_settings_snapshot"]
    snapshot["bot_diameter"] = 0.9
    snapshot["bot_step_length"] = 0.271828
    snapshot["bullet_damage"] = int(snapshot["bullet_damage"]) + 17


def alter_pre_state(payload: Payload, index: int) -> None:
    state = _play(payload, index)["pre_state"]
    first_key = next(iter(state))
    state[first_key]["x"] = 0.987654321


def alter_post_state(payload: Payload, index: int) -> None:
    state = _play(payload, index)["post_state"]
    first_key = next(iter(state))
    state[first_key]["health"] = 1


def alter_events(payload: Payload, index: int) -> None:
    events = _play(payload, index)["events"]
    if events:
        events[0]["type"] = "tampered_event"
    else:
        events.append({"type": "tampered_event", "label": "tampered"})


def delete_play(payload: Payload, index: int) -> None:
    _plays(payload).pop(index)


def reorder_plays(payload: Payload, index: int) -> None:
    plays = _plays(payload)
    other = index + 1 if index + 1 < len(plays) else index - 1
    plays[index], plays[other] = plays[other], plays[index]


def _all(_payload: Payload) -> bool:
    return True


def _full(payload: Payload) -> bool:
    return payload["privacy_mode"] == PrivacyMode.FULL.value


def _retained_request(payload: Payload) -> bool:
    return payload["privacy_mode"] != PrivacyMode.HASHED.value


PLAY_FAULTS: dict[str, tuple[Mutator, Applicability]] = {
    "alter-command": (alter_command, _all),
    "alter-response": (alter_response, _full),
    "alter-request": (alter_request, _retained_request),
    "alter-human-prompt": (alter_human_prompt, _full),
    "alter-supplied-state": (alter_supplied_state, _all),
    "alter-pre-state": (alter_pre_state, _all),
    "alter-post-state": (alter_post_state, _all),
    "alter-events": (alter_events, _all),
    "delete-play": (delete_play, _all),
    "reorder-plays": (reorder_plays, _all),
}
ROUND_FAULTS: dict[str, tuple[Mutator, Applicability]] = {
    "alter-rules": (alter_rules, _all),
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
    request_payload = request.get("payload")
    if not isinstance(request_payload, dict):
        return
    request["stored_sha256"] = sha256_json(request_payload)
    if request.get("privacy_mode") == PrivacyMode.FULL.value:
        request["canonical_sha256"] = sha256_json(request_payload)


def reanchor_trace(payload: Payload) -> None:
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


def _evaluate(
    *,
    base: Payload,
    session_name: str,
    fault: str,
    position: str,
    index: int,
    mutate: Mutator,
) -> dict[str, object]:
    payload = deepcopy(base)
    mutate(payload, index)
    reanchor_trace(payload)
    report = verify_payload(payload)
    return {
        "session": session_name,
        "privacy_mode": base["privacy_mode"],
        "fault": fault,
        "position": position,
        "play_index": index,
        "detected": not report.valid,
        "issue_codes": "|".join(sorted({issue.code for issue in report.issues})),
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    files = sorted(Path(args.corpus).glob("*.json"))
    rows: list[dict[str, object]] = []
    for path in files:
        base = json.loads(path.read_text(encoding="utf-8"))
        for name, (mutate, applicable) in PLAY_FAULTS.items():
            if not applicable(base):
                continue
            for position, index in _positions(base):
                rows.append(
                    _evaluate(
                        base=base,
                        session_name=path.name,
                        fault=name,
                        position=position,
                        index=index,
                        mutate=mutate,
                    )
                )
        for name, (mutate, applicable) in ROUND_FAULTS.items():
            if applicable(base):
                rows.append(
                    _evaluate(
                        base=base,
                        session_name=path.name,
                        fault=name,
                        position="round",
                        index=0,
                        mutate=mutate,
                    )
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
    by_position = {
        position: {
            "applicable": sum(row["position"] == position for row in rows),
            "detected": sum(
                row["position"] == position and bool(row["detected"])
                for row in rows
            ),
        }
        for position in ("early", "middle", "late", "round")
    }
    summary = {
        "sessions": len(files),
        "fault_classes": len(PLAY_FAULTS) + len(ROUND_FAULTS),
        "applicable_faults": len(rows),
        "detected": detected,
        "detection_rate": detected / len(rows),
        "by_position": by_position,
        "commitments_reanchored": True,
    }
    (results_dir / "fault-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))
    return 0 if detected == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
