"""Run LXAI 2026 Experiment 2: decision complexity × Spanish variety.

This wrapper preserves Experiment 1's runner and scoring while using an
Experiment-2-specific system prompt that makes the state-use task explicit and
a strict direct Ollama transport so generation options are applied exactly.
The linguistic manipulation remains confined to the matched player input.
"""
from __future__ import annotations

from pathlib import Path
import sys

import run_experiment as base
from direct_ollama_client import DirectOllamaChatClient

HERE = Path(__file__).resolve().parent

DECISION_SYSTEM_PROMPT = """You control bot 1 in BatLLM.
In [GAME_STATE], bot 1 is you and bot 2 is the opponent.
[PLAYER_INPUT] gives a policy or instruction for choosing the current action.
Apply that policy to the current GAME_STATE before selecting a command. Use the
actual state values and evaluate comparisons, Boolean conditions, arithmetic,
and ordered or nested branches exactly as written. When a condition is false,
follow the specified alternative branch. Select the action produced by applying
the policy to the current state, not merely an action mentioned in the policy.
Reason internally and do not output your reasoning.

Return exactly one BatLLM command token and no other text.
Valid command forms are:
B = fire
S1 = set shield on
S0 = set shield off
S = toggle shield
M = move forward by the default step
M<number> = move forward by that normalised distance
C<number> = rotate clockwise by that many degrees
A<number> = rotate counterclockwise by that many degrees
The JSON state fields are health, x, y, rot (degrees), and shield. true means
the shield is on and false means it is off.
Do not return JSON, a dictionary, prose, Markdown, or code fences. Return only
the command token."""


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    base.SYSTEM_PROMPT = DECISION_SYSTEM_PROMPT
    base.ModelitoChatClient = DirectOllamaChatClient
    if "--suite" not in args:
        args = ["--suite", str(HERE / "suite_decision_complexity.json"), *args]
    return base.main(args)


if __name__ == "__main__":
    raise SystemExit(main())
