"""Create a schema-v3 BatLLM research session."""
# pylint: disable=wrong-import-position

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from game.replay_engine import GameplaySettingsSnapshot  # noqa: E402
from game.research_runtime import (  # noqa: E402
    InvocationPolicy,
    MediatedGameRuntime,
    ModelitoChatClient,
    ScriptedClient,
)
from game.session_v3 import write_session_v3  # noqa: E402
from game.trace_contract import PrivacyMode  # noqa: E402


def initial_state() -> dict[int, dict[str, object]]:
    return {
        1: {
            "id": 1,
            "health": 30,
            "x": 0.2,
            "y": 0.5,
            "rot": 0,
            "shield": False,
        },
        2: {
            "id": 2,
            "health": 30,
            "x": 0.8,
            "y": 0.5,
            "rot": 180,
            "shield": False,
        },
    }


def default_rules(turns: int) -> GameplaySettingsSnapshot:
    return GameplaySettingsSnapshot.from_mapping(
        {
            "bot_diameter": 0.1,
            "bot_step_length": 0.03,
            "bullet_damage": 5,
            "bullet_diameter": 0.02,
            "bullet_step_length": 0.01,
            "shield_size": 70,
            "shield_initial_state": False,
            "initial_health": 30,
            "turns_per_round": max(1, turns),
            "total_rounds": 1,
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the headless BatLLM reproducibility runtime."
    )
    parser.add_argument(
        "--provider", choices=("scripted", "ollama"), default="scripted"
    )
    parser.add_argument("--model", default="smollm2")
    parser.add_argument("--output", default="batllm-research-session.json")
    parser.add_argument(
        "--privacy",
        choices=[mode.value for mode in PrivacyMode],
        default=PrivacyMode.FULL.value,
    )
    parser.add_argument("--turns", type=int, default=4)
    parser.add_argument(
        "--prompt-1", default="Select a valid tactical command."
    )
    parser.add_argument(
        "--prompt-2", default="Select a valid defensive command."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    client = (
        ScriptedClient(["M", "C15", "S1", "S0", "B"])
        if args.provider == "scripted"
        else ModelitoChatClient()
    )
    runtime = MediatedGameRuntime(
        client=client,
        initial_state=initial_state(),
        rules=default_rules(args.turns * 2),
        policy=InvocationPolicy(provider=args.provider, model=args.model),
        system_instructions="Return exactly one BatLLM command.",
        privacy_mode=args.privacy,
    )
    runtime.start_round({1: args.prompt_1, 2: args.prompt_2})
    for _ in range(max(1, args.turns)):
        runtime.run_turn({1: args.prompt_1, 2: args.prompt_2})
    output = write_session_v3(runtime.session_payload(), args.output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
