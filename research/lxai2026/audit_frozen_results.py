"""Comprehensive audit of the frozen LXAI 2026 main dataset.

This script is post-hoc descriptive analysis only. It never changes raw rows.
It consolidates language-pair comparisons, trivial suite baselines, state-use
and first-action overlap, metric-slack decomposition, output validity, response
length, repeat count, and parameter-scoring denominators.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from analyze_decision_results import canonical_command, first_terminal_command

HERE = Path(__file__).resolve().parent
DEFAULT_SUITE = HERE / "suite_decision_complexity.json"
LANGS = ("en", "es_standard", "es_rioplatense")
LABELS = {
    "en": "English",
    "es_standard": "Tuteo Spanish",
    "es_rioplatense": "Rioplatense voseo",
}


def as_bool(value: str) -> bool:
    return value == "True"


def exact_mcnemar(b: int, c: int) -> float | None:
    """Two-sided exact McNemar p-value using the conditional binomial test."""
    n = b + c
    if n == 0:
        return None
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2**n)
    return min(1.0, 2.0 * tail)


def action_family(command: str) -> str:
    c = canonical_command(command)
    if c == "B":
        return "shoot"
    if c in {"S", "S0", "S1"}:
        return "shield"
    if c.startswith("M"):
        return "move"
    if c.startswith("A") or c.startswith("C"):
        return "rotate"
    return "invalid"


def pct(n: int, d: int) -> float:
    return 100.0 * n / d if d else 0.0


def pair_metric(
    rows_by_key: dict[tuple[str, str, str], dict[str, Any]],
    left: str,
    right: str,
    metric: str,
    models: set[str] | None = None,
) -> dict[str, Any]:
    pairs: list[tuple[bool, bool]] = []
    keys = sorted({(m, case) for (m, case, _lang) in rows_by_key})
    for model, case in keys:
        if models is not None and model not in models:
            continue
        lrow = rows_by_key[(model, case, left)]
        rrow = rows_by_key[(model, case, right)]
        pairs.append((bool(lrow[metric]), bool(rrow[metric])))
    l_only = sum(l and not r for l, r in pairs)
    r_only = sum(r and not l for l, r in pairs)
    l_correct = sum(l for l, _ in pairs)
    r_correct = sum(r for _, r in pairs)
    return {
        "metric": metric,
        "pairs": len(pairs),
        "left": left,
        "right": right,
        "left_correct": l_correct,
        "right_correct": r_correct,
        "left_accuracy": l_correct / len(pairs),
        "right_accuracy": r_correct / len(pairs),
        "delta_left_minus_right": (l_correct - r_correct) / len(pairs),
        "left_only_correct": l_only,
        "right_only_correct": r_only,
        "mcnemar_exact_p": exact_mcnemar(l_only, r_only),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("results_dir", type=Path)
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    args = parser.parse_args()

    with args.suite.open(encoding="utf-8") as handle:
        suite = json.load(handle)
    cases = {c["id"]: c for c in suite["cases"]}
    if len(cases) != 48:
        raise SystemExit(f"Expected 48 suite cases, found {len(cases)}")

    rows: list[dict[str, Any]] = []
    with (args.results_dir / "results.csv").open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            row: dict[str, Any] = dict(raw)
            for key in (
                "valid",
                "action_family_correct",
                "command_correct",
                "executable_correct",
                "diagnostic_command_correct",
            ):
                row[key] = as_bool(raw[key])
            row["parameter_correct_bool"] = (
                None if raw["parameter_correct"] == "" else as_bool(raw["parameter_correct"])
            )
            row["normalized_command_canonical"] = canonical_command(raw["normalized_command"])
            row["expected_command_canonical"] = canonical_command(raw["expected_command"])
            rows.append(row)

    if len(rows) != 576:
        raise SystemExit(f"Expected 576 rows, found {len(rows)}")

    models = sorted({str(r["model"]) for r in rows})
    if len(models) != 4:
        raise SystemExit(f"Expected four models, found {models}")
    llama_models = {m for m in models if m.startswith("llama3.2")}
    non_llama_models = set(models) - llama_models

    rows_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for r in rows:
        rows_by_key[(str(r["model"]), str(r["case_id"]), str(r["condition"]))] = r

    # Language comparisons.
    pairwise: dict[str, Any] = {}
    for metric in ("command_correct", "action_family_correct", "executable_correct"):
        pairwise[metric] = {}
        for left, right in (
            ("en", "es_standard"),
            ("en", "es_rioplatense"),
            ("es_standard", "es_rioplatense"),
        ):
            key = f"{left}__vs__{right}"
            pairwise[metric][key] = pair_metric(rows_by_key, left, right, metric)

    # Same descriptive accuracies excluding Llama 3.2.
    without_llama: dict[str, Any] = {}
    for condition in LANGS:
        subset = [
            r for r in rows
            if r["condition"] == condition and r["model"] in non_llama_models
        ]
        without_llama[condition] = {
            "n": len(subset),
            "strict_correct": sum(bool(r["command_correct"]) for r in subset),
            "strict_accuracy": sum(bool(r["command_correct"]) for r in subset) / len(subset),
            "executable_correct": sum(bool(r["executable_correct"]) for r in subset),
            "executable_accuracy": sum(bool(r["executable_correct"]) for r in subset) / len(subset),
        }

    # Oracle distribution and trivial baselines on the 48 semantic/state cases.
    expected_commands = [canonical_command(c["expected"]) for c in cases.values()]
    command_counts = Counter(expected_commands)
    family_counts = Counter(action_family(c) for c in expected_commands)
    majority_command, majority_command_n = command_counts.most_common(1)[0]
    majority_family, majority_family_n = family_counts.most_common(1)[0]
    first_oracle_n = 0
    first_commands: dict[str, str] = {}
    for case_id, case in cases.items():
        first = first_terminal_command(case["en"])
        first_commands[case_id] = first
        if canonical_command(case["expected"]) == first:
            first_oracle_n += 1
    baselines = {
        "oracle_command_counts": dict(command_counts),
        "oracle_family_counts": dict(family_counts),
        "always_majority_command": {
            "command": majority_command,
            "correct": majority_command_n,
            "n": 48,
            "accuracy": majority_command_n / 48,
        },
        "always_majority_action_family": {
            "family": majority_family,
            "correct": majority_family_n,
            "n": 48,
            "accuracy": majority_family_n / 48,
        },
        "always_first_mentioned_action": {
            "correct": first_oracle_n,
            "n": 48,
            "accuracy": first_oracle_n / 48,
        },
    }

    # Policy-level state invariance and overlap with locking onto first action.
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        case = cases[str(r["case_id"])]
        groups[(str(r["model"]), str(r["condition"]), str(case["policy_id"]))].append(r)

    overlap: dict[str, Any] = {}
    for condition in LANGS:
        state_invariant = 0
        locked_first = 0
        invariant_and_first = 0
        policy_complete = 0
        n_groups = 0
        for (model, cond, policy_id), items in groups.items():
            if cond != condition:
                continue
            n_groups += 1
            outputs = {str(i["normalized_command_canonical"]) for i in items}
            expected = {str(i["expected_command_canonical"]) for i in items}
            invariant = len(outputs) == 1 and len(expected) > 1
            complete = all(bool(i["command_correct"]) for i in items)
            first = first_commands[str(items[0]["case_id"])]
            first_lock = len(outputs) == 1 and next(iter(outputs)) == first
            state_invariant += int(invariant)
            locked_first += int(first_lock)
            invariant_and_first += int(invariant and first_lock)
            policy_complete += int(complete)
        overlap[condition] = {
            "groups": n_groups,
            "policy_complete": policy_complete,
            "state_invariant": state_invariant,
            "locked_to_first_action": locked_first,
            "state_invariant_and_locked_to_first": invariant_and_first,
            "state_invariant_not_first": state_invariant - invariant_and_first,
        }

    # Strict vs executable metric slack.
    slack_rows = [r for r in rows if r["executable_correct"] and not r["command_correct"]]
    slack_by_model = Counter(str(r["model"]) for r in slack_rows)
    slack_pairs = Counter(
        (str(r["normalized_command_canonical"]), str(r["expected_command_canonical"]))
        for r in slack_rows
    )
    slack_by_model_pair: dict[str, Counter[tuple[str, str]]] = defaultdict(Counter)
    for r in slack_rows:
        slack_by_model_pair[str(r["model"])][
            (str(r["normalized_command_canonical"]), str(r["expected_command_canonical"]))
        ] += 1

    # Validity and invalid outputs.
    invalid_rows = [r for r in rows if not r["valid"]]
    invalid_by_condition = Counter(str(r["condition"]) for r in invalid_rows)
    invalid_by_model = Counter(str(r["model"]) for r in invalid_rows)
    invalid_raw = Counter(str(r["raw_response"]) for r in invalid_rows)
    max_raw_len = max(len(str(r["raw_response"])) for r in rows)
    max_raw_examples = sorted({str(r["raw_response"]) for r in rows if len(str(r["raw_response"])) == max_raw_len})

    # Diagnostic recovery and parameter metric.
    diagnostic_diff = [
        r for r in rows
        if bool(r["diagnostic_command_correct"]) != bool(r["command_correct"])
    ]
    parameter: dict[str, Any] = {}
    for model in models:
        parameter[model] = {}
        for condition in LANGS:
            applicable = [
                r for r in rows
                if r["model"] == model
                and r["condition"] == condition
                and r["parameter_correct_bool"] is not None
            ]
            parameter[model][condition] = {
                "applicable": len(applicable),
                "correct": sum(bool(r["parameter_correct_bool"]) for r in applicable),
                "accuracy": (
                    sum(bool(r["parameter_correct_bool"]) for r in applicable) / len(applicable)
                    if applicable else None
                ),
            }

    repeat_values = sorted({int(str(r["repeat"])) for r in rows})

    audit: dict[str, Any] = {
        "results_dir": str(args.results_dir),
        "n_rows": len(rows),
        "models": models,
        "repeat_values": repeat_values,
        "n_repeats_per_cell": len(repeat_values),
        "pairwise_language": pairwise,
        "without_llama": without_llama,
        "baselines": baselines,
        "policy_overlap": overlap,
        "strict_executable_slack": {
            "n": len(slack_rows),
            "by_model": dict(slack_by_model),
            "command_pairs": {f"{a}->{b}": n for (a, b), n in slack_pairs.items()},
            "by_model_command_pairs": {
                model: {f"{a}->{b}": n for (a, b), n in pairs.items()}
                for model, pairs in slack_by_model_pair.items()
            },
        },
        "invalid_outputs": {
            "n": len(invalid_rows),
            "by_condition": dict(invalid_by_condition),
            "by_model": dict(invalid_by_model),
            "raw_responses": dict(invalid_raw),
        },
        "max_raw_response_characters": max_raw_len,
        "max_raw_response_examples": max_raw_examples,
        "diagnostic_command_correct_differs_from_command_correct": len(diagnostic_diff),
        "parameter_correct": parameter,
    }

    json_path = args.results_dir / "frozen_run_audit.json"
    json_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def pstr(value: float | None) -> str:
        return "n/a" if value is None else f"{value:.4f}"

    lines: list[str] = [
        "# Frozen-run audit",
        "",
        f"Source: `{args.results_dir}`",
        "",
        "This is post-hoc descriptive audit output. It does not alter the frozen dataset.",
        "",
        "## Language-pair comparisons",
        "",
        "| Metric | Left | Right | Left acc. | Right acc. | Left-only | Right-only | Δ left−right | exact McNemar p |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for metric in ("command_correct", "action_family_correct", "executable_correct"):
        for comparison in pairwise[metric].values():
            lines.append(
                f"| {metric} | {LABELS[comparison['left']]} | {LABELS[comparison['right']]} | "
                f"{100*comparison['left_accuracy']:.1f}% | {100*comparison['right_accuracy']:.1f}% | "
                f"{comparison['left_only_correct']} | {comparison['right_only_correct']} | "
                f"{100*comparison['delta_left_minus_right']:+.1f} pp | {pstr(comparison['mcnemar_exact_p'])} |"
            )

    lines += [
        "",
        "## Trivial suite baselines",
        "",
        f"- Oracle command distribution: `{dict(command_counts)}`.",
        f"- Oracle action-family distribution: `{dict(family_counts)}`.",
        f"- Always `{majority_command}`: {majority_command_n}/48 ({pct(majority_command_n,48):.1f}%).",
        f"- Always `{majority_family}` action family: {majority_family_n}/48 ({pct(majority_family_n,48):.1f}%).",
        f"- Always first-mentioned action: {first_oracle_n}/48 ({pct(first_oracle_n,48):.1f}%).",
        "",
        "## Policy-group overlap",
        "",
        "| Condition | Complete | State-invariant | Locked to first | Invariant + first | Invariant, not first |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for condition in LANGS:
        s = overlap[condition]
        lines.append(
            f"| {LABELS[condition]} | {s['policy_complete']}/{s['groups']} | "
            f"{s['state_invariant']}/{s['groups']} | {s['locked_to_first_action']}/{s['groups']} | "
            f"{s['state_invariant_and_locked_to_first']}/{s['groups']} | "
            f"{s['state_invariant_not_first']}/{s['groups']} |"
        )

    lines += [
        "",
        "## Strict/executable discrepancy",
        "",
        f"Executable-correct but strict-command-wrong rows: **{len(slack_rows)}**.",
        f"By model: `{dict(slack_by_model)}`.",
        f"Command-pair decomposition: `{ {f'{a}->{b}': n for (a,b),n in slack_pairs.items()} }`.",
        "",
        "## Output/runner checks",
        "",
        f"- Repeat values: `{repeat_values}`; repeats per cell = {len(repeat_values)}.",
        f"- Longest raw response: {max_raw_len} characters; examples: `{max_raw_examples}`.",
        f"- Invalid rows: {len(invalid_rows)}; by condition `{dict(invalid_by_condition)}`; by model `{dict(invalid_by_model)}`; raw `{dict(invalid_raw)}`.",
        f"- `diagnostic_command_correct` differs from `command_correct` on {len(diagnostic_diff)} / {len(rows)} rows.",
        "",
        "## Pooled strict accuracy without Llama 3.2",
        "",
        "| Condition | Correct | N | Strict accuracy | Executable accuracy |",
        "|---|---:|---:|---:|---:|",
    ]
    for condition in LANGS:
        s = without_llama[condition]
        lines.append(
            f"| {LABELS[condition]} | {s['strict_correct']} | {s['n']} | "
            f"{100*s['strict_accuracy']:.1f}% | {100*s['executable_accuracy']:.1f}% |"
        )

    lines += ["", "## Parameter correctness", ""]
    lines += [
        "| Model | Condition | Applicable | Correct | Accuracy |",
        "|---|---|---:|---:|---:|",
    ]
    for model in models:
        for condition in LANGS:
            s = parameter[model][condition]
            acc = "n/a" if s["accuracy"] is None else f"{100*s['accuracy']:.1f}%"
            lines.append(
                f"| {model} | {LABELS[condition]} | {s['applicable']} | {s['correct']} | {acc} |"
            )

    md_path = args.results_dir / "FROZEN-RUN-AUDIT.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(md_path)
    print(json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
