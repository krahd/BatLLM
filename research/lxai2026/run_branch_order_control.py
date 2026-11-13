"""Run a post-freeze branch-order control for the LXAI 2026 study.

The control uses the eight binary policies from D1, D2, D3, and D5. For each,
the natural-language condition is rewritten to be logically equivalent while
reversing which terminal action is mentioned first. States, oracle commands,
models, transport, scoring, and the command-only system prompt remain unchanged.

D4/D6 priority trees are deliberately excluded: reversing their surface order
would require larger structural rewrites and would confound branch position
with policy complexity.
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
from run_decision_experiment import DECISION_SYSTEM_PROMPT  # noqa: E402

CONDITIONS = ("en", "es_standard", "es_rioplatense")
LABELS = {
    "en": "English",
    "es_standard": "Tuteo Spanish",
    "es_rioplatense": "Rioplatense voseo",
}

# Each rewrite is logically equivalent to the corresponding frozen policy but
# places the original alternative/second terminal action first.
REWRITES: dict[str, dict[str, str]] = {
    "D1-P1": {
        "en": "If your shield is down, fire; otherwise lower the shield.",
        "es_standard": "Si tienes el escudo bajo, dispara; si no, bájalo.",
        "es_rioplatense": "Si tenés el escudo bajo, dispará; si no, bajalo.",
    },
    "D1-P2": {
        "en": "If your health is 15 or higher, move forward; otherwise raise the shield.",
        "es_standard": "Si tienes 15 puntos de salud o más, avanza; si no, levanta el escudo.",
        "es_rioplatense": "Si tenés 15 puntos de salud o más, avanzá; si no, levantá el escudo.",
    },
    "D2-P1": {
        "en": "If your health is greater than or equal to the opponent's health, fire; otherwise raise the shield.",
        "es_standard": "Si tienes tanta o más salud que el rival, dispara; si no, levanta el escudo.",
        "es_rioplatense": "Si tenés tanta o más salud que el rival, dispará; si no, levantá el escudo.",
    },
    "D2-P2": {
        "en": "If your x coordinate is less than or equal to the opponent's x coordinate, turn clockwise 90 degrees; otherwise turn counterclockwise 90 degrees.",
        "es_standard": "Si tu coordenada x es menor o igual que la del rival, gira 90 grados en sentido horario; si no, gira 90 grados en sentido antihorario.",
        "es_rioplatense": "Si tu coordenada x es menor o igual que la del rival, girá 90 grados en sentido horario; si no, girá 90 grados en sentido antihorario.",
    },
    "D3-P1": {
        "en": "If your health is 15 or higher or your shield is raised, fire; otherwise raise the shield.",
        "es_standard": "Si tienes 15 puntos de salud o más o el escudo está levantado, dispara; si no, levanta el escudo.",
        "es_rioplatense": "Si tenés 15 puntos de salud o más o el escudo está levantado, dispará; si no, levantá el escudo.",
    },
    "D3-P2": {
        "en": "If both shields are in the same state, fire; otherwise move forward.",
        "es_standard": "Si los dos escudos están en el mismo estado, dispara; si no, avanza.",
        "es_rioplatense": "Si los dos escudos están en el mismo estado, dispará; si no, avanzá.",
    },
    "D5-P1": {
        "en": "If your health is not at least 10 points higher than the opponent's health, raise the shield; otherwise fire.",
        "es_standard": "Si no tienes al menos 10 puntos de salud más que el rival, levanta el escudo; si no, dispara.",
        "es_rioplatense": "Si no tenés al menos 10 puntos de salud más que el rival, levantá el escudo; si no, dispará.",
    },
    "D5-P2": {
        "en": "Compute the horizontal distance between your x coordinate and the opponent's x coordinate. If it is below 0.4, turn clockwise 90 degrees; otherwise move forward 0.1.",
        "es_standard": "Calcula la distancia horizontal entre tu coordenada x y la coordenada x del rival. Si es menor que 0.4, gira 90 grados en sentido horario; si no, avanza 0.1.",
        "es_rioplatense": "Calculá la distancia horizontal entre tu coordenada x y la coordenada x del rival. Si es menor que 0.4, girá 90 grados en sentido horario; si no, avanzá 0.1.",
    },
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
        "system_prompt_sha256": hashlib.sha256(DECISION_SYSTEM_PROMPT.encode("utf-8")).hexdigest(),
        "rewrite_map_sha256": hashlib.sha256(
            json.dumps(REWRITES, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest(),
    }


def selected_cases(suite_path: Path) -> tuple[dict[str, Any], list[base.TrialCase], dict[str, str]]:
    payload = json.loads(suite_path.read_text(encoding="utf-8"))
    original_cases = {str(item["id"]): item for item in payload["cases"]}
    _, loaded = base.load_suite(suite_path)
    output: list[base.TrialCase] = []
    policy_by_case: dict[str, str] = {}
    for case in loaded:
        policy_id = str(original_cases[case.case_id]["policy_id"])
        if policy_id not in REWRITES:
            continue
        policy_by_case[case.case_id] = policy_id
        output.append(
            base.TrialCase(
                case_id=case.case_id,
                task_class="branch_order_control",
                tier=case.tier,
                expected_command=case.expected_command,
                state=case.state,
                variants=REWRITES[policy_id],
            )
        )
    if len(output) != 32:
        raise ValueError(f"Expected 32 selected cases, found {len(output)}")
    return payload, output, policy_by_case


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run LXAI branch-order control.")
    parser.add_argument("--models", nargs="+", required=True)
    parser.add_argument("--conditions", nargs="+", choices=CONDITIONS, default=list(CONDITIONS))
    parser.add_argument("--suite", type=Path, default=HERE / "suite_decision_complexity.json")
    parser.add_argument("--host", default="http://localhost")
    parser.add_argument("--port", type=int, default=11434)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=20260825)
    parser.add_argument("--order-seed", type=int, default=20260825)
    parser.add_argument("--num-predict", type=int, default=24)
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
    output = args.output_dir or HERE / "controls" / "branch_order" / stamp
    output.mkdir(parents=True, exist_ok=True)
    metadata = {
        "experiment": "LXAI 2026 branch-order post-freeze control",
        "relation_to_main_run": (
            "Separate post-hoc control. Uses 8 binary frozen policies with logically equivalent "
            "rewrites that reverse first-mentioned terminal action. D4/D6 excluded."
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
        "system_prompt": DECISION_SYSTEM_PROMPT,
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
                {"role": "system", "content": DECISION_SYSTEM_PROMPT},
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
                raw = extract_response_text(response)
                latency = (perf_counter() - started) * 1000.0
                error = None
            except Exception as exc:
                raw = ""
                latency = (perf_counter() - started) * 1000.0
                error = f"{type(exc).__name__}: {exc}"
            parsed = parse_model_response(raw)
            score = (
                base.score_response(trial.case, raw, game_rules)
                if error is None else base.Score(False, False, False, None, False)
            )
            policy_id = policy_by_case[trial.case.case_id]
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
                "raw_response": raw,
                "normalized_command": parsed.normalized_cmd,
                "valid": score.valid,
                "command_correct": score.command_correct,
                "action_family_correct": score.action_family_correct,
                "executable_correct": score.executable_correct,
                "latency_ms": round(latency, 3),
                "error": error,
            }
            rows.append(row)
            jsonl.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            jsonl.flush()
            marker = "ERR" if error else ("OK" if score.command_correct else "MISS")
            print(
                f"[{index:>4}/{len(trials)}] {marker:4} {trial.model} {trial.condition:15} "
                f"{trial.case.case_id} -> {parsed.normalized_cmd} "
                f"(expected {row['expected_command']})"
            )

    write_csv(output / "results.csv", rows)
    summary: dict[str, Any] = {
        "n_rows": len(rows),
        "provider_errors": sum(bool(r["error"]) for r in rows),
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
            }
    (output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("\nStrict command correctness")
    for model, conditions in summary["by_model_condition"].items():
        for condition, stats in conditions.items():
            print(f"{model}\t{condition}\t{100*stats['command_correct']:.1f}%")
    print(f"\nResults: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
