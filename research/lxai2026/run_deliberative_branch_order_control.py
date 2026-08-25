"""Run the missing 2x2 interaction cell for the LXAI 2026 post-freeze controls.

This separate post-hoc control combines:
- the logically equivalent branch-order reversals from run_branch_order_control.py; and
- the explicit-deliberation / FINAL-command interface from run_deliberation_control.py.

It is intentionally limited to the eight binary policies (32 states), the two
Spanish conditions, and user-selected models. The frozen 576-call main dataset
is never modified.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
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
from game.replay_engine import parse_model_response  # noqa: E402
from game.research_runtime import extract_response_text  # noqa: E402
from run_branch_order_control import REWRITES, selected_cases  # noqa: E402
from run_deliberation_control import SYSTEM_PROMPT, extract_final_command  # noqa: E402

CONDITIONS = ("es_standard", "es_rioplatense")
LABELS = {
    "es_standard": "Tuteo Spanish",
    "es_rioplatense": "Rioplatense voseo",
}


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
        "source_suite_sha256": hashlib.sha256(suite_path.read_bytes()).hexdigest(),
        "system_prompt_sha256": hashlib.sha256(SYSTEM_PROMPT.encode("utf-8")).hexdigest(),
        "rewrite_map_sha256": hashlib.sha256(
            json.dumps(REWRITES, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest(),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run LXAI deliberative branch-order control.")
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
    suite_payload, cases, policy_by_case = selected_cases(args.suite)
    game_rules = base.rules()
    base.validate_suite(cases, game_rules)
    trials = base.build_trials(cases, models, args.conditions, args.repeats, args.order_seed, args.limit)
    print(f"Semantic cases: {len(cases)} (8 binary policies × 4 states)")
    print(f"Models: {', '.join(models)}")
    print(f"Conditions: {', '.join(args.conditions)}")
    print(f"Planned model calls: {len(trials)}")
    if args.dry_run:
        return 0

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = args.output_dir or HERE / "controls" / "deliberative_branch_order" / stamp
    output.mkdir(parents=True, exist_ok=True)

    metadata = {
        "experiment": "LXAI 2026 deliberative branch-order post-freeze control",
        "relation_to_main_run": (
            "Separate post-hoc interaction control completing the 2x2 direct/deliberative "
            "x original/reordered design on the eight binary policies. Frozen main unchanged."
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
        "source_suite": str(args.suite),
        "source_suite_version": suite_payload.get("version"),
        "rewrites": REWRITES,
        "provenance": collect_provenance(models, args.host, args.port, args.suite),
    }
    (output / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )

    client = DirectOllamaChatClient(host=args.host, port=args.port)
    rows: list[dict[str, Any]] = []
    with (output / "results.jsonl").open("w", encoding="utf-8") as jsonl:
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
            score = (
                base.score_response(trial.case, scored_response, game_rules)
                if transport_error is None and extraction_error is None
                else base.Score(False, False, False, None, False)
            )
            parsed = parse_model_response(scored_response)
            policy_id = policy_by_case[trial.case.case_id]
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
                "policy_id": policy_id,
                "tier": trial.case.tier,
                "condition": trial.condition,
                "condition_label": LABELS[trial.condition],
                "instruction": trial.case.variants[trial.condition],
                "expected_command": parse_model_response(trial.case.expected_command).normalized_cmd,
                "full_response": full_response,
                "scored_response": scored_response,
                "normalized_command": parsed.normalized_cmd,
                "valid": score.valid,
                "command_correct": score.command_correct,
                "action_family_correct": score.action_family_correct,
                "executable_correct": score.executable_correct,
                "failure_class": failure_class,
                "final_extraction_error": extraction_error,
                "latency_ms": round(latency, 3),
                "error": transport_error,
            }
            rows.append(row)
            jsonl.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            jsonl.flush()
            marker = (
                "ERR" if transport_error or extraction_error
                else "OK" if score.command_correct
                else "MISS"
            )
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
