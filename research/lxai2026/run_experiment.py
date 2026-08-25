"""Run the LXAI 2026 Rioplatense executable-action experiment.

Single entry point for matched English, broadly standardised Spanish, and
Rioplatense Spanish trials. Each invocation is stateless. Responses are parsed
with BatLLM's production command parser and executed with BatLLM's deterministic
replay semantics.

Example:
    python research/lxai2026/run_experiment.py \
        --models llama3.2 qwen3:8b mistral-small
"""
# pylint: disable=wrong-import-position,too-many-locals,too-many-statements

from __future__ import annotations

import argparse
import ast
import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import random
import statistics
import subprocess
import sys
from time import perf_counter
from typing import Any, Iterable, Mapping, Sequence
from urllib.error import URLError
from urllib.request import urlopen

# BatLLM's configuration layer imports Kivy. Disable Kivy's argv parser before
# any BatLLM import so experiment-specific flags such as --models reach argparse.
os.environ.setdefault("KIVY_NO_ARGS", "1")

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
HERE = Path(__file__).resolve().parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from game.replay_engine import (  # noqa: E402
    GameplaySettingsSnapshot,
    apply_play,
    normalize_state_map,
    parse_model_response,
)
from game.research_runtime import ModelitoChatClient, extract_response_text  # noqa: E402

CONDITIONS = ("en", "es_standard", "es_rioplatense")
LABELS = {
    "en": "English",
    "es_standard": "standardised Spanish",
    "es_rioplatense": "Rioplatense Spanish",
}
SYSTEM_PROMPT = """You control bot 1 in BatLLM.
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
The JSON state uses the fields health, x, y, rot (degrees), and shield.
true means the shield is on and false means it is off.
Do not return JSON, a dictionary, prose, Markdown, or code fences. Return only
the command token."""


@dataclass(frozen=True)
class TrialCase:
    case_id: str
    task_class: str
    tier: str
    expected_command: str
    state: Mapping[int, Mapping[str, Any]]
    variants: Mapping[str, str]


@dataclass(frozen=True)
class TrialSpec:
    model: str
    repeat: int
    case: TrialCase
    condition: str


@dataclass(frozen=True)
class Score:
    valid: bool
    command_correct: bool
    action_family_correct: bool
    parameter_correct: bool | None
    executable_correct: bool


@dataclass(frozen=True)
class Diagnostic:
    command: str | None
    method: str | None
    command_correct: bool
    failure_class: str


def state_from_overrides(overrides: Mapping[str, Any]) -> dict[int, dict[str, Any]]:
    own = {"id": 1, "health": 30, "x": 0.20, "y": 0.50, "rot": 0.0, "shield": False}
    opponent = {"id": 2, "health": 30, "x": 0.80, "y": 0.50, "rot": 180.0, "shield": False}
    for key, value in overrides.items():
        if key.startswith("opponent_"):
            opponent[key.removeprefix("opponent_")] = value
        else:
            own[key] = value
    return {1: own, 2: opponent}


def load_suite(path: Path) -> tuple[dict[str, Any], list[TrialCase]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = []
    for item in payload["cases"]:
        variants = {condition: str(item[condition]) for condition in CONDITIONS}
        cases.append(TrialCase(
            case_id=str(item["id"]), task_class=str(item["class"]), tier=str(item["tier"]),
            expected_command=str(item["expected"]),
            state=state_from_overrides(item.get("state") or {}), variants=variants,
        ))
    return payload, cases


def rules() -> GameplaySettingsSnapshot:
    return GameplaySettingsSnapshot.from_mapping({
        "bot_diameter": 0.1, "bot_step_length": 0.03, "bullet_damage": 5,
        "bullet_diameter": 0.02, "bullet_step_length": 0.01,
        "shield_size": 70, "shield_initial_state": False,
        "initial_health": 30, "turns_per_round": 1, "total_rounds": 1,
    })


def validate_suite(cases: Sequence[TrialCase], game_rules: GameplaySettingsSnapshot) -> None:
    seen = set()
    for item in cases:
        if item.case_id in seen:
            raise ValueError(f"Duplicate case_id: {item.case_id}")
        seen.add(item.case_id)
        expected = parse_model_response(item.expected_command)
        if not expected.valid:
            raise ValueError(f"Invalid expected command in {item.case_id}: {item.expected_command}")
        if not all(item.variants[condition].strip() for condition in CONDITIONS):
            raise ValueError(f"Empty linguistic condition in {item.case_id}")
        apply_play(normalize_state_map(item.state), bot_id=1, llm_response=item.expected_command,
                   cmd_text=None, rules=game_rules)


def user_message(item: TrialCase, condition: str) -> str:
    rendered = json.dumps({"bots": normalize_state_map(item.state)}, ensure_ascii=False,
                          sort_keys=True, separators=(",", ":"))
    return f"[GAME_STATE]\n{rendered}\n[PLAYER_INPUT]\n{item.variants[condition]}"


def event_signature(event: Any) -> dict[str, Any]:
    return asdict(event) if hasattr(event, "__dataclass_fields__") else {
        "type": getattr(event, "type", None), "label": getattr(event, "label", None),
        "bot_id": getattr(event, "bot_id", None),
        "target_bot_id": getattr(event, "target_bot_id", None),
        "details": getattr(event, "details", None),
    }


def states_equal(left, right, tol=1e-9) -> bool:
    a, b = normalize_state_map(left), normalize_state_map(right)
    if set(a) != set(b):
        return False
    for bot_id in a:
        if any(a[bot_id][key] != b[bot_id][key] for key in ("health", "shield")):
            return False
        if any(not math.isclose(float(a[bot_id][key]), float(b[bot_id][key]),
                                rel_tol=0.0, abs_tol=tol) for key in ("x", "y", "rot")):
            return False
    return True


def score_response(item: TrialCase, raw: str, game_rules: GameplaySettingsSnapshot) -> Score:
    actual, expected = parse_model_response(raw), parse_model_response(item.expected_command)
    parameter_correct = None if expected.value is None else bool(
        actual.valid and actual.value is not None
        and math.isclose(actual.value, expected.value, rel_tol=0.0, abs_tol=1e-9)
    )
    game_state = normalize_state_map(item.state)
    expected_run = apply_play(game_state, bot_id=1, llm_response=item.expected_command,
                              cmd_text=None, rules=game_rules)
    actual_run = apply_play(game_state, bot_id=1, llm_response=raw,
                            cmd_text=None, rules=game_rules)
    executable_correct = bool(
        actual.valid and states_equal(actual_run.state_by_bot, expected_run.state_by_bot)
        and [event_signature(event) for event in actual_run.events]
        == [event_signature(event) for event in expected_run.events]
    )
    return Score(
        valid=actual.valid,
        command_correct=actual.valid and actual.normalized_cmd == expected.normalized_cmd,
        action_family_correct=actual.valid and actual.kind == expected.kind,
        parameter_correct=parameter_correct,
        executable_correct=executable_correct,
    )


def recover_wrapped_command(raw: str) -> tuple[str | None, str | None]:
    """Recover an unambiguous command for diagnostics without changing execution.

    The primary metrics always use BatLLM's strict production parser. This
    diagnostic only recognises a mapping with a string-valued ``command`` key,
    covering outputs such as ``{'command': 'S1'}``. It deliberately does not
    search arbitrary prose for command-looking substrings.
    """
    strict = parse_model_response(raw)
    if strict.valid:
        return strict.normalized_cmd, "strict"
    text = str(raw or "").strip()
    for loader, method in ((json.loads, "json_command_field"),
                           (ast.literal_eval, "literal_command_field")):
        try:
            payload = loader(text)
        except (ValueError, SyntaxError, TypeError):
            continue
        if not isinstance(payload, Mapping) or not isinstance(payload.get("command"), str):
            continue
        candidate = parse_model_response(payload["command"])
        if candidate.valid:
            return candidate.normalized_cmd, method
    return None, None


def diagnostic(item: TrialCase, raw: str, score: Score, error: str | None) -> Diagnostic:
    if error is not None:
        return Diagnostic(None, None, False, "provider_error")
    expected = parse_model_response(item.expected_command).normalized_cmd
    recovered, method = recover_wrapped_command(raw)
    recovered_correct = recovered == expected if recovered is not None else False
    if score.command_correct:
        failure_class = "correct"
    elif not score.valid and recovered_correct:
        failure_class = "format_only"
    elif not score.valid and recovered is not None:
        failure_class = "format_and_action_error"
    elif score.valid:
        failure_class = "action_error"
    else:
        failure_class = "invalid_unrecoverable"
    return Diagnostic(recovered, method, recovered_correct, failure_class)


def build_trials(cases, models, conditions, repeats, order_seed, limit=None) -> list[TrialSpec]:
    """Randomise case and condition order while preserving complete case groups."""
    conditions = list(conditions)
    if limit is not None and int(limit) % len(conditions) != 0:
        raise ValueError(
            f"--limit must be divisible by the number of conditions ({len(conditions)}) "
            "so smoke tests preserve matched cases."
        )
    all_trials = []
    for model_index, model in enumerate(models):
        rng = random.Random(order_seed + model_index)
        groups = [(repeat, item) for repeat in range(repeats) for item in cases]
        rng.shuffle(groups)
        batch = []
        for repeat, item in groups:
            condition_order = conditions[:]
            rng.shuffle(condition_order)
            batch.extend(TrialSpec(model, repeat, item, condition) for condition in condition_order)
        all_trials.extend(batch)
    return all_trials if limit is None else all_trials[:max(0, int(limit))]


def invoke(client, model, item, condition, options):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message(item, condition)},
    ]
    started = perf_counter()
    try:
        response = client.chat(model=model, messages=messages, options=dict(options), stream=False)
        return extract_response_text(response), (perf_counter() - started) * 1000.0, None
    except Exception as exc:  # live-provider boundary; preserve failed calls as rows
        return "", (perf_counter() - started) * 1000.0, f"{type(exc).__name__}: {exc}"


def mean_bool(rows: Iterable[Mapping[str, Any]], key: str):
    values = [float(bool(row[key])) for row in rows if row.get(key) is not None]
    return statistics.fmean(values) if values else None


def exact_mcnemar_p(standard_only: int, rio_only: int):
    n = standard_only + rio_only
    if not n:
        return None
    k = min(standard_only, rio_only)
    return min(1.0, 2.0 * sum(math.comb(n, i) for i in range(k + 1)) / (2**n))


def paired(rows, metric, model=None, task_class=None, tier=None):
    index = {}
    for row in rows:
        if row.get("error") or row["condition"] not in {"es_standard", "es_rioplatense"}:
            continue
        if model is not None and row["model"] != model:
            continue
        if task_class is not None and row["task_class"] != task_class:
            continue
        if tier is not None and row["tier"] != tier:
            continue
        key = (row["model"], row["repeat"], row["case_id"])
        index.setdefault(key, {})[row["condition"]] = bool(row[metric])
    pairs = [(value["es_standard"], value["es_rioplatense"]) for value in index.values()
             if "es_standard" in value and "es_rioplatense" in value]
    standard_only = sum(1 for standard, rio in pairs if standard and not rio)
    rio_only = sum(1 for standard, rio in pairs if not standard and rio)
    standard = statistics.fmean(float(value) for value, _ in pairs) if pairs else None
    rio = statistics.fmean(float(value) for _, value in pairs) if pairs else None
    return {
        "metric": metric, "pairs": len(pairs), "standard_accuracy": standard,
        "rioplatense_accuracy": rio,
        "delta_standard_minus_rioplatense": None if standard is None else standard - rio,
        "standard_only_correct": standard_only, "rioplatense_only_correct": rio_only,
        "mcnemar_exact_p": exact_mcnemar_p(standard_only, rio_only),
    }


def summarise(rows, models):
    metrics = ("valid", "action_family_correct", "parameter_correct",
               "command_correct", "executable_correct", "diagnostic_command_correct")
    summary = {
        "n_rows": len(rows),
        "errors": sum(bool(row.get("error")) for row in rows),
        "failure_classes": {
            key: sum(row.get("failure_class") == key for row in rows)
            for key in ("correct", "format_only", "format_and_action_error", "action_error",
                        "invalid_unrecoverable", "provider_error")
        },
        "by_model_condition": {},
        "paired_standard_vs_rioplatense": {},
    }
    for model in models:
        summary["by_model_condition"][model] = {}
        for condition in CONDITIONS:
            subset = [row for row in rows if row["model"] == model
                      and row["condition"] == condition and not row.get("error")]
            summary["by_model_condition"][model][condition] = {
                "n": len(subset), **{metric: mean_bool(subset, metric) for metric in metrics}
            }
    task_classes = sorted({row["task_class"] for row in rows})
    tiers = sorted({row["tier"] for row in rows})
    for metric in ("valid", "action_family_correct", "command_correct", "executable_correct",
                   "diagnostic_command_correct"):
        summary["paired_standard_vs_rioplatense"][metric] = {
            "all_models": paired(rows, metric),
            "by_model": {model: paired(rows, metric, model=model) for model in models},
            "by_task_class": {value: paired(rows, metric, task_class=value) for value in task_classes},
            "by_tier": {value: paired(rows, metric, tier=value) for value in tiers},
        }
    return summary


def write_csv(path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def rate(value):
    return "n/a" if value is None else f"{100 * float(value):.1f}%"


def print_summary(summary):
    print("\nStrict command correctness by model and condition")
    print("model\tEnglish\tstandard Spanish\tRioplatense\tstd-rio")
    for model, conditions in summary["by_model_condition"].items():
        standard = conditions["es_standard"]["command_correct"]
        rio = conditions["es_rioplatense"]["command_correct"]
        delta = None if standard is None or rio is None else standard - rio
        print(f"{model}\t{rate(conditions['en']['command_correct'])}\t{rate(standard)}"
              f"\t{rate(rio)}\t{rate(delta)}")
    comparison = summary["paired_standard_vs_rioplatense"]["command_correct"]["all_models"]
    print("\nPaired standardised-Spanish vs Rioplatense strict command correctness")
    print(json.dumps(comparison, indent=2, ensure_ascii=False))
    print("\nFailure classes")
    print(json.dumps(summary["failure_classes"], indent=2, ensure_ascii=False))


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
    model_records = {}
    for requested in models:
        matched = next(
            (
                item for item in available
                if isinstance(item, Mapping)
                and requested in {str(item.get("name") or ""), str(item.get("model") or "")}
            ),
            None,
        )
        model_records[requested] = dict(matched) if isinstance(matched, Mapping) else None
    version_payload = _ollama_json(host, port, "/api/version") or {}
    suite_bytes = suite_path.read_bytes()
    return {
        "git_commit": _command_output(("git", "rev-parse", "HEAD")),
        "git_branch": _command_output(("git", "branch", "--show-current")),
        "python_version": sys.version,
        "python_executable": sys.executable,
        "ollama_version": version_payload.get("version") or _command_output(("ollama", "--version")),
        "models": model_records,
        "suite_sha256": hashlib.sha256(suite_bytes).hexdigest(),
        "system_prompt_sha256": hashlib.sha256(SYSTEM_PROMPT.encode("utf-8")).hexdigest(),
    }


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Run the LXAI Rioplatense BatLLM action-fidelity experiment.")
    value.add_argument("--models", nargs="+", required=True, help="Installed Ollama model names.")
    value.add_argument("--conditions", nargs="+", choices=CONDITIONS, default=list(CONDITIONS))
    value.add_argument("--suite", type=Path, default=HERE / "suite.json")
    value.add_argument("--host", default="http://localhost")
    value.add_argument("--port", type=int, default=11434)
    value.add_argument("--temperature", type=float, default=0.0)
    value.add_argument("--seed", type=int, default=20260825)
    value.add_argument("--order-seed", type=int, default=20260825)
    value.add_argument("--num-predict", type=int, default=24)
    value.add_argument("--repeats", type=int, default=1)
    value.add_argument("--output-dir", type=Path)
    value.add_argument(
        "--limit", type=int,
        help="Run only N invocations; N must preserve complete condition sets for each case.",
    )
    value.add_argument("--dry-run", action="store_true")
    return value


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    if args.repeats < 1 or args.num_predict < 1:
        raise SystemExit("--repeats and --num-predict must be positive.")
    models = [model.strip() for model in args.models if model.strip()]
    suite_payload, cases = load_suite(args.suite)
    game_rules = rules()
    validate_suite(cases, game_rules)
    trials = build_trials(cases, models, args.conditions, args.repeats, args.order_seed, args.limit)
    print(f"Semantic cases: {len(cases)}")
    print(f"Models: {', '.join(models)}")
    print(f"Conditions: {', '.join(args.conditions)}")
    print(f"Planned model calls: {len(trials)}")
    if args.dry_run:
        return 0

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = args.output_dir or HERE / "results" / stamp
    output.mkdir(parents=True, exist_ok=True)
    metadata = {
        "experiment": "LXAI 2026 Rioplatense executable-action fidelity",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "models": models, "conditions": args.conditions, "condition_labels": LABELS,
        "n_semantic_cases": len(cases), "n_invocations_planned": len(trials),
        "repeats": args.repeats, "temperature": args.temperature, "seed": args.seed,
        "order_seed": args.order_seed, "num_predict": args.num_predict,
        "host": args.host, "port": args.port, "rules": game_rules.to_dict(),
        "system_prompt": SYSTEM_PROMPT, "suite_source": str(args.suite),
        "suite_version": suite_payload.get("version"), "suite_status": suite_payload.get("status"),
        "provenance": collect_provenance(models, args.host, args.port, args.suite),
        "primary_metric_note": (
            "Strict metrics use BatLLM's production parser unchanged. Diagnostic command recovery "
            "is reported separately and never changes executable scoring."
        ),
        "suite": [{
            "case_id": item.case_id, "task_class": item.task_class, "tier": item.tier,
            "expected_command": item.expected_command, "state": normalize_state_map(item.state),
            "variants": dict(item.variants),
        } for item in cases],
    }
    (output / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True),
                                          encoding="utf-8")

    client, rows = ModelitoChatClient(host=args.host, port=args.port), []
    result_path = output / "results.jsonl"
    with result_path.open("w", encoding="utf-8") as jsonl:
        for index, trial in enumerate(trials, 1):
            options = {"temperature": args.temperature, "seed": args.seed + trial.repeat,
                       "num_predict": args.num_predict}
            raw, latency, error = invoke(client, trial.model, trial.case, trial.condition, options)
            parsed = parse_model_response(raw)
            score = score_response(trial.case, raw, game_rules) if error is None else Score(False, False, False, None, False)
            diag = diagnostic(trial.case, raw, score, error)
            row = {
                "model": trial.model, "repeat": trial.repeat, "case_id": trial.case.case_id,
                "task_class": trial.case.task_class, "tier": trial.case.tier,
                "condition": trial.condition, "condition_label": LABELS[trial.condition],
                "instruction": trial.case.variants[trial.condition],
                "expected_command": parse_model_response(trial.case.expected_command).normalized_cmd,
                "raw_response": raw, "normalized_command": parsed.normalized_cmd,
                "parsed_kind": parsed.kind, "parsed_value": parsed.value,
                "valid": score.valid, "action_family_correct": score.action_family_correct,
                "parameter_correct": score.parameter_correct, "command_correct": score.command_correct,
                "executable_correct": score.executable_correct,
                "diagnostic_command": diag.command,
                "diagnostic_method": diag.method,
                "diagnostic_command_correct": diag.command_correct,
                "failure_class": diag.failure_class,
                "latency_ms": round(latency, 3), "error": error,
            }
            rows.append(row)
            jsonl.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            jsonl.flush()
            marker = "ERR" if error else ("OK" if score.command_correct else "MISS")
            diagnostic_suffix = ""
            if not score.command_correct and diag.command is not None:
                diagnostic_suffix = f"; diagnostic={diag.command}/{diag.failure_class}"
            print(f"[{index:>4}/{len(trials)}] {marker:4} {trial.model} {trial.condition:15} "
                  f"{trial.case.case_id} -> {parsed.normalized_cmd} (expected {row['expected_command']})"
                  f"{diagnostic_suffix}")

    write_csv(output / "results.csv", rows)
    summary = summarise(rows, models)
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
                                         encoding="utf-8")
    print_summary(summary)
    if summary["errors"]:
        print(f"\nProvider errors recorded: {summary['errors']}")
    print(f"\nResults: {output}")
    return 0 if not summary["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
