"""Differentially test BatLLM gameplay against an independent reference model."""

from __future__ import annotations

import argparse
import json
import random
from typing import Any

from common import ROOT
from game.replay_engine import GameplaySettingsSnapshot, apply_play, parse_model_response
from game.trace_contract import canonical_json, event_to_dict
from reference_semantics import (
    ReferenceRules,
    apply_reference,
    parse_command,
    paths_equivalent,
    states_equivalent,
)


def _rules(rng: random.Random, index: int) -> dict[str, Any]:
    return {
        "bot_diameter": rng.choice((0.06, 0.08, 0.1, 0.14)),
        "bot_step_length": rng.choice((0.01, 0.03, 0.05, 0.12)),
        "bullet_damage": rng.choice((1, 3, 5, 9)),
        "bullet_diameter": 0.02,
        "bullet_step_length": rng.choice((0.005, 0.01, 0.02)),
        "shield_size": rng.choice((35, 55, 70, 95)),
        "shield_initial_state": False,
        "initial_health": 30,
        "turns_per_round": 1 + index % 20,
        "total_rounds": 1,
    }


def _state(rng: random.Random) -> dict[int, dict[str, Any]]:
    return {
        1: {
            "id": 1,
            "health": rng.randint(1, 30),
            "x": rng.uniform(0.06, 0.94),
            "y": rng.uniform(0.06, 0.94),
            "rot": rng.uniform(-720, 720),
            "shield": rng.choice((False, True)),
        },
        2: {
            "id": 2,
            "health": rng.randint(1, 30),
            "x": rng.uniform(0.06, 0.94),
            "y": rng.uniform(0.06, 0.94),
            "rot": rng.uniform(-720, 720),
            "shield": rng.choice((False, True)),
        },
    }


def _command(rng: random.Random, index: int) -> str:
    choices = (
        "M",
        f"M{rng.uniform(-0.2, 0.3):.8f}",
        f"C{rng.uniform(-720, 720):.8f}",
        f"A{rng.uniform(-720, 720):.8f}",
        "S",
        "S1",
        "S0",
        "B",
        "nonsense",
        "Mbad",
        "Cbad",
        "Awrong",
        "Sx",
        "",
    )
    return choices[index % len(choices)]


def _targeted_cases() -> list[tuple[dict[int, dict[str, Any]], int, str, dict[str, Any]]]:
    base_rules = {
        "bot_diameter": 0.1,
        "bot_step_length": 0.03,
        "bullet_damage": 5,
        "bullet_diameter": 0.02,
        "bullet_step_length": 0.01,
        "shield_size": 70,
        "shield_initial_state": False,
        "initial_health": 30,
        "turns_per_round": 1,
        "total_rounds": 1,
    }
    return [
        (
            {
                1: {"id": 1, "health": 30, "x": 0.2, "y": 0.5, "rot": 0, "shield": False},
                2: {"id": 2, "health": 30, "x": 0.8, "y": 0.5, "rot": 180, "shield": False},
            },
            1,
            "B",
            base_rules,
        ),
        (
            {
                1: {"id": 1, "health": 30, "x": 0.2, "y": 0.5, "rot": 0, "shield": False},
                2: {"id": 2, "health": 30, "x": 0.8, "y": 0.5, "rot": 180, "shield": True},
            },
            1,
            "B",
            base_rules,
        ),
        (
            {
                1: {"id": 1, "health": 30, "x": 0.2, "y": 0.5, "rot": 0, "shield": True},
                2: {"id": 2, "health": 30, "x": 0.8, "y": 0.5, "rot": 180, "shield": False},
            },
            1,
            "B",
            base_rules,
        ),
        (
            {
                1: {"id": 1, "health": 30, "x": 0.2, "y": 0.2, "rot": 90, "shield": False},
                2: {"id": 2, "health": 30, "x": 0.8, "y": 0.8, "rot": 180, "shield": False},
            },
            1,
            "B",
            base_rules,
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260721)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cases < len(_targeted_cases()):
        raise ValueError("--cases is smaller than the targeted-case set")
    rng = random.Random(args.seed)
    cases = list(_targeted_cases())
    while len(cases) < args.cases:
        index = len(cases)
        cases.append((_state(rng), 1 + index % 2, _command(rng, index), _rules(rng, index)))

    normalization_matches = 0
    state_matches = 0
    event_matches = 0
    path_matches = 0
    mismatches: list[dict[str, Any]] = []

    for index, (state, bot_id, response, rules_map) in enumerate(cases):
        production_parsed = parse_model_response(response)
        reference_parsed = parse_command(response)
        normalization_ok = (
            production_parsed.normalized_cmd == reference_parsed.normalized
            and production_parsed.valid == reference_parsed.valid
        )
        normalization_matches += int(normalization_ok)

        production = apply_play(
            state,
            bot_id=bot_id,
            llm_response=response,
            cmd_text=None,
            rules=GameplaySettingsSnapshot.from_mapping(rules_map),
        )
        reference = apply_reference(
            state,
            bot_id=bot_id,
            response=response,
            rules=ReferenceRules.from_mapping(rules_map),
        )
        state_ok = states_equivalent(production.state_by_bot, reference.state_by_bot)
        production_events = [event_to_dict(event) for event in production.events]
        event_ok = canonical_json(production_events) == canonical_json(reference.events)
        path_ok = paths_equivalent(production.shot_path, reference.shot_path)
        state_matches += int(state_ok)
        event_matches += int(event_ok)
        path_matches += int(path_ok)
        if not (normalization_ok and state_ok and event_ok and path_ok):
            mismatches.append(
                {
                    "case": index,
                    "response": response,
                    "bot_id": bot_id,
                    "normalization_ok": normalization_ok,
                    "state_ok": state_ok,
                    "event_ok": event_ok,
                    "path_ok": path_ok,
                    "production_command": production.normalized_cmd,
                    "reference_command": reference.normalized_command,
                }
            )
            if len(mismatches) >= 20:
                break

    summary = {
        "seed": args.seed,
        "cases": args.cases,
        "normalization_matches": normalization_matches,
        "state_matches": state_matches,
        "event_matches": event_matches,
        "path_matches": path_matches,
        "mismatch_count": len(mismatches),
        "reference_imports_production_gameplay": False,
        "mismatches": mismatches,
    }
    output = ROOT / "research/urucon2026/results/differential-summary.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    complete = (
        normalization_matches == args.cases
        and state_matches == args.cases
        and event_matches == args.cases
        and path_matches == args.cases
        and not mismatches
    )
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
