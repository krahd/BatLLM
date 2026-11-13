"""Analyse the post-freeze 2x2 interface × branch-order control.

Cells on the eight binary policies:
1. direct-command × original order       (frozen main subset)
2. direct-command × reversed order       (branch-order control)
3. deliberative × original order         (deliberation control subset)
4. deliberative × reversed order         (deliberative-branch-order control)

The analysis is descriptive and never mutates any raw result file.
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


def latest_child(path: Path) -> Path:
    children = sorted((p for p in path.iterdir() if p.is_dir()), key=lambda p: p.name)
    if not children:
        raise SystemExit(f"No result directories under {path}")
    return children[-1]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def truth(value: str) -> bool:
    return value == "True"


def load_suite(path: Path) -> tuple[dict[str, str], dict[str, str], set[str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    policy_by_case: dict[str, str] = {}
    original_first: dict[str, str] = {}
    selected_cases: set[str] = set()
    for item in payload["cases"]:
        policy = str(item["policy_id"])
        case = str(item["id"])
        policy_by_case[case] = policy
        original_first.setdefault(policy, first_terminal_command(str(item["en"])))
        if policy in REWRITES:
            selected_cases.add(case)
    if len(selected_cases) != 32:
        raise AssertionError(len(selected_cases))
    return policy_by_case, original_first, selected_cases


def first_for(policy: str, order: str, original_first: dict[str, str]) -> str:
    if order == "original":
        return canonical_command(original_first[policy])
    return canonical_command(first_terminal_command(REWRITES[policy]["en"]))


def diagnostics(
    rows: list[dict[str, str]],
    policy_by_case: dict[str, str],
    original_first: dict[str, str],
    order: str,
) -> dict[str, Any]:
    groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    first_selected = 0
    for row in rows:
        policy = policy_by_case[row["case_id"]]
        groups[(row["model"], row["condition"], policy)].append(row)
        first = first_for(policy, order, original_first)
        first_selected += int(canonical_command(row["normalized_command"]) == first)

    complete = invariant = 0
    for items in groups.values():
        expected = {canonical_command(i["expected_command"]) for i in items}
        outputs = {canonical_command(i["normalized_command"]) for i in items}
        complete += int(all(truth(i["command_correct"]) for i in items))
        invariant += int(len(expected) > 1 and len(outputs) == 1)

    return {
        "n": len(rows),
        "correct": sum(truth(r["command_correct"]) for r in rows),
        "accuracy": sum(truth(r["command_correct"]) for r in rows) / len(rows),
        "first_selected": first_selected,
        "first_rate": first_selected / len(rows),
        "policy_groups": len(groups),
        "policy_complete": complete,
        "state_invariant": invariant,
        "provider_errors": sum(bool(r.get("error")) for r in rows),
        "extraction_errors": sum(bool(r.get("final_extraction_error")) for r in rows),
    }


def pair_order_changes(
    original: list[dict[str, str]],
    reordered: list[dict[str, str]],
    policy_by_case: dict[str, str],
    original_first: dict[str, str],
) -> dict[str, Any]:
    index = {(r["model"], r["condition"], r["case_id"]): r for r in original}
    changed = changed_to_new_first = 0
    for row in reordered:
        key = (row["model"], row["condition"], row["case_id"])
        before = index[key]
        bcmd = canonical_command(before["normalized_command"])
        acmd = canonical_command(row["normalized_command"])
        did_change = bcmd != acmd
        changed += int(did_change)
        policy = policy_by_case[row["case_id"]]
        new_first = first_for(policy, "reordered", original_first)
        changed_to_new_first += int(did_change and acmd == new_first)
    return {
        "n": len(reordered),
        "output_changed": changed,
        "changed_to_new_first": changed_to_new_first,
        "changed_to_new_first_given_change": (
            changed_to_new_first / changed if changed else None
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", type=Path, default=DEFAULT_MAIN)
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--direct-reordered", type=Path)
    parser.add_argument("--deliberative-original", type=Path)
    parser.add_argument("--deliberative-reordered", type=Path)
    args = parser.parse_args(argv)

    direct_reordered_dir = args.direct_reordered or latest_child(HERE / "controls" / "branch_order")
    deliberative_original_dir = args.deliberative_original or latest_child(HERE / "controls" / "deliberation")
    deliberative_reordered_dir = args.deliberative_reordered or latest_child(
        HERE / "controls" / "deliberative_branch_order"
    )

    policy_by_case, original_first, selected_cases = load_suite(args.suite)
    spanish = {"es_standard", "es_rioplatense"}

    main_all = read_csv(args.main / "results.csv")
    dorig_all = read_csv(deliberative_original_dir / "results.csv")
    dreord_all = read_csv(direct_reordered_dir / "results.csv")
    dbreord_all = read_csv(deliberative_reordered_dir / "results.csv")

    models = sorted({r["model"] for r in dbreord_all})
    model_set = set(models)

    def filt(rows: list[dict[str, str]]) -> list[dict[str, str]]:
        return [
            r for r in rows
            if r["model"] in model_set
            and r["condition"] in spanish
            and r["case_id"] in selected_cases
        ]

    cells = {
        "direct_original": filt(main_all),
        "direct_reordered": filt(dreord_all),
        "deliberative_original": filt(dorig_all),
        "deliberative_reordered": filt(dbreord_all),
    }
    expected_n = 32 * len(models) * 2
    for name, rows in cells.items():
        if len(rows) != expected_n:
            raise SystemExit(f"{name}: expected {expected_n} rows, found {len(rows)}")

    output: dict[str, Any] = {
        "models": models,
        "conditions": sorted(spanish),
        "n_per_cell": expected_n,
        "cells": {
            "direct_original": diagnostics(cells["direct_original"], policy_by_case, original_first, "original"),
            "direct_reordered": diagnostics(cells["direct_reordered"], policy_by_case, original_first, "reordered"),
            "deliberative_original": diagnostics(cells["deliberative_original"], policy_by_case, original_first, "original"),
            "deliberative_reordered": diagnostics(cells["deliberative_reordered"], policy_by_case, original_first, "reordered"),
        },
        "order_change": {
            "direct": pair_order_changes(
                cells["direct_original"], cells["direct_reordered"], policy_by_case, original_first
            ),
            "deliberative": pair_order_changes(
                cells["deliberative_original"], cells["deliberative_reordered"], policy_by_case, original_first
            ),
        },
        "directories": {
            "main": str(args.main),
            "direct_reordered": str(direct_reordered_dir),
            "deliberative_original": str(deliberative_original_dir),
            "deliberative_reordered": str(deliberative_reordered_dir),
        },
    }

    out_json = HERE / "controls" / "INTERFACE-ORDER-FACTORIAL.json"
    out_md = HERE / "controls" / "INTERFACE-ORDER-FACTORIAL.md"
    out_json.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Interface × branch-order factorial analysis",
        "",
        f"Models: {', '.join(models)}",
        "Conditions: tuteo and Rioplatense voseo",
        f"Rows per cell: {expected_n}",
        "",
        "| Interface | Order | Accuracy | First-position selection | Policy-complete | State-invariant |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for name in (
        "direct_original", "direct_reordered", "deliberative_original", "deliberative_reordered"
    ):
        s = output["cells"][name]
        interface, order = name.split("_", 1)
        lines.append(
            f"| {interface} | {order} | {100*s['accuracy']:.1f}% | {s['first_selected']}/{s['n']} "
            f"({100*s['first_rate']:.1f}%) | {s['policy_complete']}/{s['policy_groups']} | "
            f"{s['state_invariant']}/{s['policy_groups']} |"
        )
    lines += ["", "Order-swap response changes:", ""]
    for interface, s in output["order_change"].items():
        rate = "n/a" if s["changed_to_new_first_given_change"] is None else f"{100*s['changed_to_new_first_given_change']:.1f}%"
        lines.append(
            f"- {interface}: outputs changed {s['output_changed']}/{s['n']}; "
            f"changed to newly first-mentioned action {s['changed_to_new_first']}/{s['output_changed']} ({rate})."
        )
    lines += [
        "",
        "This is a post-freeze descriptive interaction analysis. It does not alter the frozen main dataset.",
        "",
    ]
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(out_md)
    print(out_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
