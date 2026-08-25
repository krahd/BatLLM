"""Post-hoc descriptive diagnostics for the frozen LXAI 2026 main dataset.

This script does not modify raw result rows. It derives the prospectively declared
policy-complete, state-invariance, and first-mentioned-action diagnostics from a
completed results directory plus the frozen decision suite.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DEFAULT_SUITE = HERE / "suite_decision_complexity.json"


def canonical_command(command: str) -> str:
    raw = command.strip()
    if not raw:
        return raw
    head = raw[0].upper()
    if head in {"A", "C"} and len(raw) > 1:
        return f"{head}{float(raw[1:])}"
    if head == "M" and len(raw) > 1:
        return f"M{float(raw[1:])}"
    return raw.upper()


def first_terminal_command(english_instruction: str) -> str:
    """Return the first action mentioned in the English policy as a BatLLM command."""
    text = english_instruction.lower()
    candidates: list[tuple[int, str]] = []

    def add(pattern: str, command: str) -> None:
        match = re.search(pattern, text)
        if match:
            candidates.append((match.start(), canonical_command(command)))

    add(r"lower (?:it|the shield|your shield)", "S0")
    add(r"raise (?:the |your )?shield", "S1")
    add(r"fire", "B")
    add(r"turn counterclockwise\s+([0-9.]+)\s+degrees", "A90")
    add(r"turn clockwise\s+([0-9.]+)\s+degrees", "C90")

    move_match = re.search(r"move forward(?:\s+([0-9.]+))?", text)
    if move_match:
        distance = move_match.group(1)
        candidates.append(
            (move_match.start(), canonical_command("M" if distance is None else f"M{distance}"))
        )

    if not candidates:
        raise ValueError(f"Could not identify first action in: {english_instruction!r}")
    return min(candidates, key=lambda item: item[0])[1]


def pct(num: int, den: int) -> float:
    return 100.0 * num / den if den else 0.0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("results_dir", type=Path)
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    args = parser.parse_args()

    with args.suite.open(encoding="utf-8") as handle:
        suite = json.load(handle)
    cases = {case["id"]: case for case in suite["cases"]}

    rows: list[dict[str, Any]] = []
    with (args.results_dir / "results.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            case = cases[row["case_id"]]
            row["policy_id"] = case["policy_id"]
            row["state_variant"] = case["state_variant"]
            row["first_terminal_command"] = first_terminal_command(case["en"])
            row["command_correct_bool"] = row["command_correct"] == "True"
            row["normalized_command_canonical"] = canonical_command(row["normalized_command"])
            row["expected_command_canonical"] = canonical_command(row["expected_command"])
            rows.append(row)

    if len(rows) != 576:
        raise SystemExit(f"Expected 576 rows, found {len(rows)}")

    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["model"], row["condition"], row["policy_id"])].append(row)

    group_records: list[dict[str, Any]] = []
    for (model, condition, policy_id), items in sorted(grouped.items()):
        if len(items) != 4:
            raise SystemExit(f"Expected four states for {(model, condition, policy_id)}, got {len(items)}")
        outputs = {item["normalized_command_canonical"] for item in items}
        expected = {item["expected_command_canonical"] for item in items}
        first = items[0]["first_terminal_command"]
        first_selected = sum(item["normalized_command_canonical"] == first for item in items)
        first_oracle = sum(item["expected_command_canonical"] == first for item in items)
        group_records.append(
            {
                "model": model,
                "condition": condition,
                "policy_id": policy_id,
                "tier": policy_id.split("-")[0],
                "policy_complete": all(item["command_correct_bool"] for item in items),
                "state_invariant_output": len(outputs) == 1 and len(expected) > 1,
                "n_distinct_outputs": len(outputs),
                "n_distinct_oracle_commands": len(expected),
                "first_terminal_command": first,
                "first_action_selection_rate": first_selected / 4,
                "first_action_oracle_rate": first_oracle / 4,
            }
        )

    def summarise(records: list[dict[str, Any]]) -> dict[str, Any]:
        n = len(records)
        pc = sum(bool(r["policy_complete"]) for r in records)
        si = sum(bool(r["state_invariant_output"]) for r in records)
        first_sel = sum(float(r["first_action_selection_rate"]) for r in records) / n
        first_oracle = sum(float(r["first_action_oracle_rate"]) for r in records) / n
        return {
            "n_policy_groups": n,
            "policy_complete_n": pc,
            "policy_complete_rate": pc / n,
            "state_invariant_n": si,
            "state_invariant_rate": si / n,
            "mean_first_action_selection_rate": first_sel,
            "mean_first_action_oracle_rate": first_oracle,
            "first_action_excess": first_sel - first_oracle,
        }

    spanish = [r for r in group_records if r["condition"] in {"es_standard", "es_rioplatense"}]
    output: dict[str, Any] = {
        "results_dir": str(args.results_dir),
        "n_rows": len(rows),
        "all_conditions": summarise(group_records),
        "spanish_conditions": summarise(spanish),
        "by_condition": {},
        "by_model_condition": {},
        "by_tier_condition": {},
        "policy_groups": group_records,
    }

    for condition in sorted({r["condition"] for r in group_records}):
        output["by_condition"][condition] = summarise(
            [r for r in group_records if r["condition"] == condition]
        )
    for model in sorted({r["model"] for r in group_records}):
        output["by_model_condition"][model] = {}
        for condition in sorted({r["condition"] for r in group_records}):
            output["by_model_condition"][model][condition] = summarise(
                [r for r in group_records if r["model"] == model and r["condition"] == condition]
            )
    for tier in ["D1", "D2", "D3", "D4", "D5", "D6"]:
        output["by_tier_condition"][tier] = {}
        for condition in sorted({r["condition"] for r in group_records}):
            output["by_tier_condition"][tier][condition] = summarise(
                [r for r in group_records if r["tier"] == tier and r["condition"] == condition]
            )

    json_path = args.results_dir / "decision_analysis.json"
    json_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# LXAI decision diagnostics",
        "",
        f"Source: `{args.results_dir}`",
        "",
        "## Policy-level diagnostics by condition",
        "",
        "| Condition | Policy-complete | State-invariant | First-action selected | Oracle first-action | Excess |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    labels = {"en": "English", "es_standard": "Standard Spanish", "es_rioplatense": "Rioplatense"}
    for condition in ["en", "es_standard", "es_rioplatense"]:
        s = output["by_condition"][condition]
        lines.append(
            f"| {labels[condition]} | {s['policy_complete_n']}/{s['n_policy_groups']} "
            f"({pct(s['policy_complete_n'], s['n_policy_groups']):.1f}%) | "
            f"{s['state_invariant_n']}/{s['n_policy_groups']} "
            f"({pct(s['state_invariant_n'], s['n_policy_groups']):.1f}%) | "
            f"{100*s['mean_first_action_selection_rate']:.1f}% | "
            f"{100*s['mean_first_action_oracle_rate']:.1f}% | "
            f"{100*s['first_action_excess']:+.1f} pp |"
        )

    lines += ["", "## Spanish conditions by model", ""]
    lines += [
        "| Model | Condition | Policy-complete | State-invariant | First-action excess |",
        "|---|---|---:|---:|---:|",
    ]
    for model, conditions in output["by_model_condition"].items():
        for condition in ["es_standard", "es_rioplatense"]:
            s = conditions[condition]
            lines.append(
                f"| {model} | {labels[condition]} | "
                f"{s['policy_complete_n']}/{s['n_policy_groups']} "
                f"({pct(s['policy_complete_n'], s['n_policy_groups']):.1f}%) | "
                f"{s['state_invariant_n']}/{s['n_policy_groups']} "
                f"({pct(s['state_invariant_n'], s['n_policy_groups']):.1f}%) | "
                f"{100*s['first_action_excess']:+.1f} pp |"
            )

    lines += ["", "## Spanish conditions by decision tier", ""]
    lines += [
        "| Tier | Condition | Policy-complete | State-invariant | First-action excess |",
        "|---|---|---:|---:|---:|",
    ]
    for tier, conditions in output["by_tier_condition"].items():
        for condition in ["es_standard", "es_rioplatense"]:
            s = conditions[condition]
            lines.append(
                f"| {tier} | {labels[condition]} | "
                f"{s['policy_complete_n']}/{s['n_policy_groups']} "
                f"({pct(s['policy_complete_n'], s['n_policy_groups']):.1f}%) | "
                f"{s['state_invariant_n']}/{s['n_policy_groups']} "
                f"({pct(s['state_invariant_n'], s['n_policy_groups']):.1f}%) | "
                f"{100*s['first_action_excess']:+.1f} pp |"
            )

    md_path = args.results_dir / "DECISION-ANALYSIS.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(md_path)
    print(json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
