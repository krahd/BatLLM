"""Analyse the clean LXAI symmetric clause-order interface factorial."""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def latest_child(path: Path) -> Path | None:
    if not path.exists():
        return None
    children = sorted((p for p in path.iterdir() if p.is_dir()), key=lambda p: p.name)
    return children[-1] if children else None


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def b(value: str) -> bool:
    return value == "True"


def pct(n: int, d: int) -> str:
    return "n/a" if not d else f"{100*n/d:.1f}%"


def aggregate(rows: list[dict[str, str]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    keys = sorted({(r["interface"], r["order"], r["language"], r["model"]) for r in rows})
    for interface, order, language, model in keys:
        subset = [
            r for r in rows
            if r["interface"] == interface and r["order"] == order
            and r["language"] == language and r["model"] == model
        ]
        n = len(subset)
        out.setdefault(interface, {}).setdefault(order, {}).setdefault(language, {})[model] = {
            "n": n,
            "correct": sum(b(r["command_correct"]) for r in subset),
            "valid": sum(b(r["valid"]) for r in subset),
            "first_position": sum(b(r["selected_first_position"]) for r in subset),
            "second_position": sum(b(r["selected_second_position"]) for r in subset),
            "provider_errors": sum(bool(r.get("provider_error")) for r in subset),
            "extraction_errors": sum(bool(r.get("final_extraction_error")) for r in subset),
            "mean_latency_ms": statistics.fmean(float(r["latency_ms"]) for r in subset),
            "median_latency_ms": statistics.median(float(r["latency_ms"]) for r in subset),
            "mean_response_chars": statistics.fmean(len(r.get("full_response", "")) for r in subset),
        }
    return out


def order_pairs(rows: list[dict[str, str]]) -> dict[str, Any]:
    index: dict[tuple[str, str, str, str, str], dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        key = (row["model"], row["language"], row["interface"], row["case_id"], row["repeat"])
        index[key][row["order"]] = row

    result: dict[str, Any] = {}
    for (model, language, interface, _, _), pair in index.items():
        if "a_first" not in pair or "b_first" not in pair:
            continue
        a, b_row = pair["a_first"], pair["b_first"]
        bucket = result.setdefault(interface, {}).setdefault(language, {}).setdefault(model, {
            "pairs": 0,
            "same_output": 0,
            "output_changed": 0,
            "correct_both": 0,
            "wrong_both": 0,
            "accuracy_changed": 0,
            "follows_first_in_both": 0,
            "follows_second_in_both": 0,
            "a_first_correct": 0,
            "b_first_correct": 0,
        })
        bucket["pairs"] += 1
        changed = a["normalized_command"] != b_row["normalized_command"]
        bucket["output_changed"] += int(changed)
        bucket["same_output"] += int(not changed)
        ca, cb = b(a["command_correct"]), b(b_row["command_correct"])
        bucket["correct_both"] += int(ca and cb)
        bucket["wrong_both"] += int(not ca and not cb)
        bucket["accuracy_changed"] += int(ca != cb)
        bucket["a_first_correct"] += int(ca)
        bucket["b_first_correct"] += int(cb)
        bucket["follows_first_in_both"] += int(
            b(a["selected_first_position"]) and b(b_row["selected_first_position"])
        )
        bucket["follows_second_in_both"] += int(
            b(a["selected_second_position"]) and b(b_row["selected_second_position"])
        )
    return result


def policy_diagnostics(rows: list[dict[str, str]]) -> dict[str, Any]:
    groups: dict[tuple[str, str, str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = (
            row["model"], row["language"], row["interface"], row["order"],
            row["policy_id"], row["repeat"],
        )
        groups[key].append(row)
    out: dict[str, Any] = {}
    for (model, language, interface, order, _, _), items in groups.items():
        bucket = out.setdefault(interface, {}).setdefault(order, {}).setdefault(language, {}).setdefault(model, {
            "groups": 0,
            "complete": 0,
            "state_invariant": 0,
        })
        bucket["groups"] += 1
        bucket["complete"] += int(all(b(r["command_correct"]) for r in items))
        expected = {r["expected_command"] for r in items}
        outputs = {r["normalized_command"] for r in items}
        bucket["state_invariant"] += int(len(expected) > 1 and len(outputs) == 1)
    return out


def pooled_interface(rows: list[dict[str, str]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for interface in sorted({r["interface"] for r in rows}):
        subset = [r for r in rows if r["interface"] == interface]
        n = len(subset)
        out[interface] = {
            "n": n,
            "correct": sum(b(r["command_correct"]) for r in subset),
            "first_position": sum(b(r["selected_first_position"]) for r in subset),
            "valid": sum(b(r["valid"]) for r in subset),
            "mean_latency_ms": statistics.fmean(float(r["latency_ms"]) for r in subset),
            "median_latency_ms": statistics.median(float(r["latency_ms"]) for r in subset),
            "mean_response_chars": statistics.fmean(len(r.get("full_response", "")) for r in subset),
        }
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path)
    args = parser.parse_args(argv)
    run = args.run or latest_child(HERE / "controls" / "symmetric_clause_factorial")
    if run is None:
        raise SystemExit("No symmetric clause-order run found.")
    rows = read_rows(run / "results.csv")

    output = {
        "run": str(run),
        "n_rows": len(rows),
        "aggregate": aggregate(rows),
        "order_pairs": order_pairs(rows),
        "policy_diagnostics": policy_diagnostics(rows),
        "pooled_interface": pooled_interface(rows),
        "provider_errors": sum(bool(r.get("provider_error")) for r in rows),
        "final_extraction_errors": sum(bool(r.get("final_extraction_error")) for r in rows),
    }
    json_path = HERE / "controls" / "SYMMETRIC-CLAUSE-FACTORIAL.json"
    json_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Symmetric clause-order interface factorial",
        "",
        f"Run: `{run}`",
        f"Rows: {len(rows)}; provider errors: {output['provider_errors']}; final extraction errors: {output['final_extraction_errors']}",
        "",
        "## Pooled interface result",
        "",
        "| Interface | Correct | First-position selection | Valid | Median latency | Mean response chars |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for interface, s in output["pooled_interface"].items():
        lines.append(
            f"| {interface} | {s['correct']}/{s['n']} ({pct(s['correct'], s['n'])}) | "
            f"{s['first_position']}/{s['n']} ({pct(s['first_position'], s['n'])}) | "
            f"{s['valid']}/{s['n']} ({pct(s['valid'], s['n'])}) | "
            f"{s['median_latency_ms']:.0f} ms | {s['mean_response_chars']:.1f} |"
        )

    lines += [
        "",
        "## Order-pair sensitivity",
        "",
        "Each pair is the same model/language/interface/state with the exact same two policy clauses in opposite order.",
        "",
        "| Interface | Language | Model | Pairs | Output changed | Correct both orders | Follows first in both orders |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for interface, langs in output["order_pairs"].items():
        for language, models in langs.items():
            for model, s in models.items():
                lines.append(
                    f"| {interface} | {language} | {model} | {s['pairs']} | "
                    f"{s['output_changed']}/{s['pairs']} ({pct(s['output_changed'], s['pairs'])}) | "
                    f"{s['correct_both']}/{s['pairs']} ({pct(s['correct_both'], s['pairs'])}) | "
                    f"{s['follows_first_in_both']}/{s['pairs']} ({pct(s['follows_first_in_both'], s['pairs'])}) |"
                )

    lines += ["", "## Policy diagnostics", ""]
    lines.append("| Interface | Order | Language | Model | Complete | State-invariant |")
    lines.append("|---|---|---|---|---:|---:|")
    for interface, orders in output["policy_diagnostics"].items():
        for order, langs in orders.items():
            for language, models in langs.items():
                for model, s in models.items():
                    lines.append(
                        f"| {interface} | {order} | {language} | {model} | "
                        f"{s['complete']}/{s['groups']} | {s['state_invariant']}/{s['groups']} |"
                    )

    md_path = HERE / "controls" / "SYMMETRIC-CLAUSE-FACTORIAL.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(md_path)
    print(json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
