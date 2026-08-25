"""Analyse the LXAI 2026 post-freeze controls against the frozen main run.

The script is descriptive and keeps main and control datasets separate. It can
auto-select the latest deliberation and branch-order result directories.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from analyze_decision_results import canonical_command, first_terminal_command
from run_branch_order_control import REWRITES

HERE = Path(__file__).resolve().parent
DEFAULT_MAIN = HERE / "results" / "20260825T094526Z"
DEFAULT_SUITE = HERE / "suite_decision_complexity.json"


def latest_child(path: Path) -> Path | None:
    if not path.exists():
        return None
    children = sorted((p for p in path.iterdir() if p.is_dir()), key=lambda p: p.name)
    return children[-1] if children else None


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def b(value: str) -> bool:
    return value == "True"


def load_policy_map(suite_path: Path) -> tuple[dict[str, str], dict[str, str]]:
    payload = json.loads(suite_path.read_text(encoding="utf-8"))
    policy_by_case: dict[str, str] = {}
    original_first_by_policy: dict[str, str] = {}
    for item in payload["cases"]:
        case_id = str(item["id"])
        policy_id = str(item["policy_id"])
        policy_by_case[case_id] = policy_id
        original_first_by_policy.setdefault(policy_id, first_terminal_command(str(item["en"])))
    return policy_by_case, original_first_by_policy


def policy_diagnostics(
    rows: list[dict[str, str]], policy_by_case: dict[str, str]
) -> dict[str, Any]:
    groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[(row["model"], row["condition"], policy_by_case[row["case_id"]])].append(row)
    by_condition: dict[str, Any] = {}
    for condition in sorted({r["condition"] for r in rows}):
        chosen = [items for (model, cond, policy), items in groups.items() if cond == condition]
        complete = 0
        invariant = 0
        for items in chosen:
            expected = {canonical_command(i["expected_command"]) for i in items}
            outputs = {canonical_command(i["normalized_command"]) for i in items}
            complete += int(all(b(i["command_correct"]) for i in items))
            invariant += int(len(expected) > 1 and len(outputs) == 1)
        by_condition[condition] = {
            "groups": len(chosen),
            "policy_complete": complete,
            "state_invariant": invariant,
        }
    return by_condition


def paired_change(
    main_index: dict[tuple[str, str, str], dict[str, str]],
    control_rows: list[dict[str, str]],
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for model in sorted({r["model"] for r in control_rows}):
        out[model] = {}
        for condition in sorted({r["condition"] for r in control_rows}):
            subset = [r for r in control_rows if r["model"] == model and r["condition"] == condition]
            pairs = [(main_index[(model, r["case_id"], condition)], r) for r in subset]
            main_correct = sum(b(m["command_correct"]) for m, _ in pairs)
            ctrl_correct = sum(b(c["command_correct"]) for _, c in pairs)
            main_only = sum(b(m["command_correct"]) and not b(c["command_correct"]) for m, c in pairs)
            ctrl_only = sum(not b(m["command_correct"]) and b(c["command_correct"]) for m, c in pairs)
            changed_output = sum(
                canonical_command(m["normalized_command"]) != canonical_command(c["normalized_command"])
                for m, c in pairs
            )
            out[model][condition] = {
                "n": len(pairs),
                "main_correct": main_correct,
                "control_correct": ctrl_correct,
                "main_accuracy": main_correct / len(pairs),
                "control_accuracy": ctrl_correct / len(pairs),
                "delta_control_minus_main": (ctrl_correct - main_correct) / len(pairs),
                "main_only_correct": main_only,
                "control_only_correct": ctrl_only,
                "output_changed": changed_output,
            }
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", type=Path, default=DEFAULT_MAIN)
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--deliberation", type=Path)
    parser.add_argument("--branch-order", type=Path)
    args = parser.parse_args(argv)

    deliberation = args.deliberation or latest_child(HERE / "controls" / "deliberation")
    branch = args.branch_order or latest_child(HERE / "controls" / "branch_order")
    if deliberation is None and branch is None:
        raise SystemExit("No post-freeze control directories found.")

    main_rows = read_csv(args.main / "results.csv")
    main_index = {(r["model"], r["case_id"], r["condition"]): r for r in main_rows}
    policy_by_case, original_first = load_policy_map(args.suite)

    output: dict[str, Any] = {
        "frozen_main": str(args.main),
        "deliberation": None,
        "branch_order": None,
    }

    if deliberation is not None:
        rows = read_csv(deliberation / "results.csv")
        output["deliberation"] = {
            "directory": str(deliberation),
            "paired_change": paired_change(main_index, rows),
            "policy_diagnostics": policy_diagnostics(rows, policy_by_case),
            "provider_errors": sum(bool(r.get("error")) for r in rows),
            "final_extraction_errors": sum(bool(r.get("final_extraction_error")) for r in rows),
            "max_full_response_chars": max(len(r.get("full_response", "")) for r in rows),
        }

    if branch is not None:
        rows = read_csv(branch / "results.csv")
        selected_policy_ids = set(REWRITES)
        branch_metrics: dict[str, Any] = {}
        for model in sorted({r["model"] for r in rows}):
            branch_metrics[model] = {}
            for condition in sorted({r["condition"] for r in rows}):
                subset = [r for r in rows if r["model"] == model and r["condition"] == condition]
                n = len(subset)
                main_new_first = 0
                control_new_first = 0
                main_original_first = 0
                control_original_first = 0
                output_changed = 0
                changed_to_new_first = 0
                for ctrl in subset:
                    policy_id = policy_by_case[ctrl["case_id"]]
                    if policy_id not in selected_policy_ids:
                        raise AssertionError(policy_id)
                    main_row = main_index[(model, ctrl["case_id"], condition)]
                    orig_first = original_first[policy_id]
                    new_first = first_terminal_command(REWRITES[policy_id]["en"])
                    if orig_first == new_first:
                        raise AssertionError(f"First action did not reverse for {policy_id}")
                    mcmd = canonical_command(main_row["normalized_command"])
                    ccmd = canonical_command(ctrl["normalized_command"])
                    main_original_first += int(mcmd == orig_first)
                    main_new_first += int(mcmd == new_first)
                    control_original_first += int(ccmd == orig_first)
                    control_new_first += int(ccmd == new_first)
                    changed = mcmd != ccmd
                    output_changed += int(changed)
                    changed_to_new_first += int(changed and ccmd == new_first)
                branch_metrics[model][condition] = {
                    "n": n,
                    "main_original_first": main_original_first,
                    "main_new_first": main_new_first,
                    "control_original_first": control_original_first,
                    "control_new_first": control_new_first,
                    "output_changed": output_changed,
                    "changed_to_new_first": changed_to_new_first,
                }
        output["branch_order"] = {
            "directory": str(branch),
            "paired_change": paired_change(main_index, rows),
            "policy_diagnostics": policy_diagnostics(rows, policy_by_case),
            "position_tracking": branch_metrics,
            "provider_errors": sum(bool(r.get("error")) for r in rows),
        }

    output_path = HERE / "controls" / "POSTFREEZE-CONTROL-ANALYSIS.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Post-freeze control analysis",
        "",
        f"Frozen main: `{args.main}`",
        "",
    ]
    if output["deliberation"] is not None:
        d = output["deliberation"]
        lines += ["## Explicit-deliberation control", "", f"Directory: `{d['directory']}`", ""]
        lines += [
            "| Model | Condition | Main | Deliberation | Δ | Main-only | Control-only | Output changed |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
        for model, conditions in d["paired_change"].items():
            for condition, s in conditions.items():
                lines.append(
                    f"| {model} | {condition} | {100*s['main_accuracy']:.1f}% | "
                    f"{100*s['control_accuracy']:.1f}% | {100*s['delta_control_minus_main']:+.1f} pp | "
                    f"{s['main_only_correct']} | {s['control_only_correct']} | {s['output_changed']}/{s['n']} |"
                )
        lines += ["", "Policy diagnostics:", ""]
        for condition, s in d["policy_diagnostics"].items():
            lines.append(
                f"- `{condition}`: complete {s['policy_complete']}/{s['groups']}; "
                f"state-invariant {s['state_invariant']}/{s['groups']}."
            )
        lines += [
            "",
            f"Provider errors: {d['provider_errors']}; final-line extraction errors: {d['final_extraction_errors']}; "
            f"max full response length: {d['max_full_response_chars']} characters.",
            "",
        ]

    if output["branch_order"] is not None:
        bdata = output["branch_order"]
        lines += ["## Branch-order control", "", f"Directory: `{bdata['directory']}`", ""]
        lines += [
            "| Model | Condition | Main | Reordered | Δ | Output changed | New-first after reorder |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
        for model, conditions in bdata["paired_change"].items():
            for condition, s in conditions.items():
                pos = bdata["position_tracking"][model][condition]
                lines.append(
                    f"| {model} | {condition} | {100*s['main_accuracy']:.1f}% | "
                    f"{100*s['control_accuracy']:.1f}% | {100*s['delta_control_minus_main']:+.1f} pp | "
                    f"{pos['output_changed']}/{pos['n']} | {pos['control_new_first']}/{pos['n']} |"
                )
        lines += ["", "Position-tracking details:", ""]
        for model, conditions in bdata["position_tracking"].items():
            for condition, s in conditions.items():
                lines.append(
                    f"- `{model}` / `{condition}`: original-first main {s['main_original_first']}/{s['n']}; "
                    f"new-first after reorder {s['control_new_first']}/{s['n']}; "
                    f"changed-to-new-first {s['changed_to_new_first']}/{s['n']}."
                )
        lines += ["", f"Provider errors: {bdata['provider_errors']}.", ""]

    md_path = HERE / "controls" / "POSTFREEZE-CONTROL-ANALYSIS.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(md_path)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
