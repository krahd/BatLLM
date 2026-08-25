"""Run a post-freeze explicit-deliberation control for the LXAI 2026 study.

This is a separate control, not part of the frozen 576-call main dataset.
It uses the exact frozen decision suite and exact model checkpoints while
relaxing only the output protocol: the model may produce a short textual
scratchpad and must finish with `FINAL: <command>`. The full provider response
is preserved, while scoring uses only the extracted final command.

The Qwen3 *Instruct-2507* checkpoints used in the main experiment are
non-thinking models. This control therefore tests explicit deliberation
prompting / command-only interface sensitivity; it is not a hidden-thinking
switch for those checkpoints.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from time import perf_counter
from typing import Any, Mapping, Sequence
from urllib.error import URLError
from urllib.request import urlopen

os.environ.setdefault("KIVY_NO_ARGS", "1")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import run_experiment as base  # noqa: E402
from direct_ollama_client import DirectOllamaChatClient  # noqa: E402
from game.replay_engine import normalize_state_map, parse_model_response  # noqa: E402
from game.research_runtime import extract_response_text  # noqa: E402

CONDITIONS = ("es_standard", "es_rioplatense")
LABELS = {
    "es_standard": "Tuteo Spanish",
    "es_rioplatense": "Rioplatense voseo",
}

SYSTEM_PROMPT = """You control bot 1 in BatLLM.
In [GAME_STATE], bot 1 is you and bot 2 is the opponent.
[PLAYER_INPUT] gives a policy for choosing the current action.

Work through the supplied state and policy explicitly before choosing the
command. Check every comparison, Boolean condition, arithmetic operation and
ordered or nested branch needed by the policy. You may write a short scratchpad.

Finish with one line in exactly this form:
FINAL: <command>

where <command> is exactly one valid BatLLM command token:
B = fire
S1 = set shield on
S0 = set shield off
S = toggle shield
M = move forward by the default step
M<number> = move forward by that normalised distance
C<number> = rotate clockwise by that many degrees
A<number> = rotate counterclockwise by that many degrees

The JSON state fields are health, x, y, rot (degrees), and shield. true means
the shield is on and false means it is off. Put nothing after the FINAL line."""

FINAL_RE = re.compile(r"(?im)^\s*FINAL:\s*(\S+)\s*$")


def extract_final_command(text: str) -> tuple[str, str | None]:
    """Return (scored command text, extraction error)."""
    matches = FINAL_RE.findall(str(text or ""))
    if len(matches) != 1:
        return "", f"expected exactly one FINAL line, found {len(matches)}"
    candidate = matches[0].strip()
    parsed = parse_model_response(candidate)
    if not parsed.valid:
        return candidate, f"FINAL token is not a valid BatLLM command: {candidate!r}"
    return candidate, None


def _command_output(args: Sequence[str]) -> str | None:
    try:
        completed = subprocess.run(
            list(args), cwd=ROOT, capture_output=True, text=True, check=False, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or completed.stderr.strip() or None


def _ollama_base_url(host: str, port: int) -> str:
    clean = str(host).rstrip("/")
    suffix = f":{int(port)}"
    return clean if clean.endswith(suffix) else clean + suffix


def _ollama_json(host: str, port: int, path: str) -> dict[str, Any] | None:
    try:
        with urlopen(_ollama_base_url(host, port) + path, timeout=5) as response:  # nosec B310
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def collect_provenance(models: Sequence[str], host: str, port: int, suite_path: Path) -> dict[str, Any]:
    tags_payload = _ollama_json(host, port, "/api/tags") or {}
    available = tags_payload.get("models") if isinstance(tags_payload.get("models"), list) else []
    records: dict[str, Any] = {}
    for requested in models:
        matched = next(
            (
                item for item in available
                if isinstance(item, Mapping)
                and requested in {str(item.get("name") or ""), str(item.get("model") or "")}
            ),
            None,
        )
        records[requested] = dict(matched) if isinstance(matched, Mapping) else None
    return {
        "git_commit": _command_output(("git", "rev-parse", "HEAD")),
        "git_branch": _command_output(("git", "branch", "--show-current")),
        "python_version": sys.version,
        "ollama_version": (_ollama_json(host, port, "/api/version") or {}).get("version"),
        "models": records,
        "suite_sha256": hashlib.sha256(suite_path.read_bytes()).hexdigest(),
        "system_prompt_sha256": hashlib.sha256(SYSTEM_PROMPT.encode("utf-8")).hexdigest(),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run LXAI explicit-deliberation control.")
    parser.add_argument("--models", nargs="+", required=True)
    parser.add_argument("--conditions", nargs="+", choices=CONDITIONS, default=list(CONDITIONS))
    parser.add_argument("--suite", type=Path, default=HERE / "suite_decision_complexity.json")
    parser.add_argument("--host", default="http://localhost")
    parser.add_argument("--port", type=int, default=11434)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=20260825)
    parser.add_argument("--order-seed", type=int, default=20260825)
    parser.add_argument("--num-predict", type=int, default=256)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    models = [m.strip() for m in args.models if m.strip()]
    suite_payload, cases = base.load_suite(args.suite)
    game_rules = base.rules()
    base.validate_suite(cases, game_rules)
    trials = base.build_trials(
        cases, models, args.conditions, args.repeats, args.order_seed, args.limit
    )
    print(f"Semantic cases: {len(cases)}")
    print(f"Models: {', '.join(models)}")
    print(f"Conditions: {', '.join(args.conditions)}")
    print(f"Planned model calls: {len(trials)}")
    if args.dry_run:
        return 0

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = args.output_dir or HERE / "controls" / "deliberation" / stamp
    output.mkdir(parents=True, exist_ok=True)

    metadata = {
        "experiment": "LXAI 2026 explicit-deliberation post-freeze control",
        "relation_to_main_run": (
            "Separate post-hoc control. Frozen 20260825T094526Z main data are unchanged. "
            "Same suite/checkpoints; explicit textual deliberation and FINAL-command protocol."
        ),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "models": models,
        "conditions": args.conditions,
        "condition_labels": LABELS,
        "n_semantic_cases": len(cases),
        "n_invocations_planned": len(trials),
        "repeats": args.repeats,
        "temperature": args.temperature,
        "seed": args.seed,
        "order_seed": args.order_seed,
        "num_predict": args.num_predict,
        "host": args.host,
        "port": args.port,
        "rules": game_rules.to_dict(),
        "system_prompt": SYSTEM_PROMPT,
        "suite_source": str(args.suite),
        "suite_version": suite_payload.get("version"),
        "provenance": collect_provenance(models, args.host, args.port, args.suite),
    }
    (output / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )

    client = DirectOllamaChatClient(host=args.host, port=args.port)
    rows: list[dict[str, Any]] = []
    result_path = output / "results.jsonl"
    with result_path.open("w", encoding="utf-8") as jsonl:
        for index, trial in enumerate(trials, 1):
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": base.user_message(trial.case, trial.condition)},
            ]
            options = {
                "temperature": args.temperature,
                "seed": args.seed + trial.repeat,
                "num_predict": args.num_predict,
            }
            started = perf_counter()
            try:
                response = client.chat(
                    model=trial.model, messages=messages, options=options, stream=False
                )
                full_response = extract_response_text(response)
                latency = (perf_counter() - started) * 1000.0
                transport_error = None
            except Exception as exc:
                full_response = ""
                latency = (perf_counter() - started) * 1000.0
                transport_error = f"{type(exc).__name__}: {exc}"

            scored_response, extraction_error = (
                extract_final_command(full_response) if transport_error is None else ("", None)
            )
            error = transport_error
            score = (
                base.score_response(trial.case, scored_response, game_rules)
                if error is None and extraction_error is None
                else base.Score(False, False, False, None, False)
            )
            parsed = parse_model_response(scored_response)
            failure_class = (
                "provider_error" if transport_error
                else "final_extraction_error" if extraction_error
                else "correct" if score.command_correct
                else "action_error" if score.valid
                else "invalid_final_command"
            )
            row = {
                "model": trial.model,
                "repeat": trial.repeat,
                "case_id": trial.case.case_id,
                "task_class": trial.case.task_class,
                "tier": trial.case.tier,
                "condition": trial.condition,
                "condition_label": LABELS[trial.condition],
                "instruction": trial.case.variants[trial.condition],
                "expected_command": parse_model_response(trial.case.expected_command).normalized_cmd,
                "full_response": full_response,
                "scored_response": scored_response,
                "normalized_command": parsed.normalized_cmd,
                "valid": score.valid,
                "action_family_correct": score.action_family_correct,
                "parameter_correct": score.parameter_correct,
                "command_correct": score.command_correct,
                "executable_correct": score.executable_correct,
                "failure_class": failure_class,
                "final_extraction_error": extraction_error,
                "latency_ms": round(latency, 3),
                "error": error,
            }
            rows.append(row)
            jsonl.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            jsonl.flush()
            marker = "ERR" if error or extraction_error else ("OK" if score.command_correct else "MISS")
            print(
                f"[{index:>4}/{len(trials)}] {marker:4} {trial.model} {trial.condition:15} "
                f"{trial.case.case_id} -> {parsed.normalized_cmd} "
                f"(expected {row['expected_command']})"
            )

    write_csv(output / "results.csv", rows)

    summary: dict[str, Any] = {
        "n_rows": len(rows),
        "provider_errors": sum(bool(r["error"]) for r in rows),
        "final_extraction_errors": sum(bool(r["final_extraction_error"]) for r in rows),
        "by_model_condition": {},
    }
    for model in models:
        summary["by_model_condition"][model] = {}
        for condition in args.conditions:
            subset = [r for r in rows if r["model"] == model and r["condition"] == condition]
            n = len(subset)
            summary["by_model_condition"][model][condition] = {
                "n": n,
                "command_correct": sum(bool(r["command_correct"]) for r in subset) / n,
                "executable_correct": sum(bool(r["executable_correct"]) for r in subset) / n,
                "valid_final": sum(bool(r["valid"]) for r in subset) / n,
            }
    (output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("\nStrict command correctness")
    for model, conditions in summary["by_model_condition"].items():
        for condition, stats in conditions.items():
            print(f"{model}\t{condition}\t{100*stats['command_correct']:.1f}%")
    print(f"\nResults: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
