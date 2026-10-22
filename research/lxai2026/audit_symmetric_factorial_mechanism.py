"""Mechanism audit for the completed clean LXAI symmetric clause-order factorial.

This script adds no model calls.  It derives the position-vs-truth split, Wilson
intervals, response-length diagnostics and extraction-failure distribution from
the committed 512-row factorial.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def latest_child(path: Path) -> Path | None:
    children = sorted((p for p in path.iterdir() if p.is_dir()), key=lambda p: p.name) if path.exists() else []
    return children[-1] if children else None


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def b(v: str) -> bool:
    return v == "True"


def wilson(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return centre - half, centre + half


def describe_lengths(values: list[int]) -> dict[str, float | int]:
    if not values:
        return {"n": 0}
    vals = sorted(values)
    return {
        "n": len(vals),
        "mean": statistics.fmean(vals),
        "median": statistics.median(vals),
        "min": vals[0],
        "max": vals[-1],
        "p99_nearest_rank": vals[max(0, math.ceil(0.99 * len(vals)) - 1)],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path)
    args = parser.parse_args(argv)
    run = args.run or latest_child(HERE / "controls" / "symmetric_clause_factorial")
    if run is None:
        raise SystemExit("No symmetric clause factorial run found")
    rows = read_rows(run / "results.csv")

    out: dict[str, Any] = {"run": str(run), "n_rows": len(rows)}

    # Central truth-position decomposition.
    truth_split: dict[str, Any] = {}
    for interface in ("direct", "deliberative"):
        sub = [r for r in rows if r["interface"] == interface]
        first_truth = [r for r in sub if r["expected_command"] == r["first_position_command"]]
        second_truth = [r for r in sub if r["expected_command"] == r["second_position_command"]]
        if len(first_truth) + len(second_truth) != len(sub):
            raise AssertionError("Expected action is not one of the two clause actions")
        def pack(items: list[dict[str, str]]) -> dict[str, Any]:
            correct = sum(b(r["command_correct"]) for r in items)
            lo, hi = wilson(correct, len(items))
            return {"n": len(items), "correct": correct, "accuracy": correct/len(items), "wilson95": [lo, hi]}
        valid = [r for r in sub if b(r["valid"])]
        first_selected = sum(b(r["selected_first_position"]) for r in sub)
        first_selected_valid = sum(b(r["selected_first_position"]) for r in valid)
        truth_split[interface] = {
            "oracle_is_first": pack(first_truth),
            "oracle_is_second": pack(second_truth),
            "first_position_selected": first_selected,
            "first_position_selected_rate": first_selected / len(sub),
            "first_position_selected_among_valid": first_selected_valid / len(valid) if valid else None,
            "valid": len(valid),
            "balanced_oracle_first": len(first_truth) == len(second_truth),
            "position_only_expected_accuracy_if_ignores_state": 0.5 if len(first_truth) == len(second_truth) else None,
        }
    out["truth_position_split"] = truth_split

    # Extraction failure / response length diagnostic for deliberative arm.
    drows = [r for r in rows if r["interface"] == "deliberative"]
    failures = [r for r in drows if bool(r.get("final_extraction_error"))]
    successes = [r for r in drows if not bool(r.get("final_extraction_error"))]
    out["deliberative_length_diagnostic"] = {
        "failed_extraction": describe_lengths([len(r.get("full_response", "")) for r in failures]),
        "successful_extraction": describe_lengths([len(r.get("full_response", "")) for r in successes]),
        "failure_by_model_language_order": {},
        "response_chars_by_model_language": {},
        "failed_response_suffixes": [r.get("full_response", "")[-80:] for r in failures],
    }
    counts: dict[tuple[str,str,str], int] = defaultdict(int)
    for r in failures:
        counts[(r["model"], r["language"], r["order"])] += 1
    out["deliberative_length_diagnostic"]["failure_by_model_language_order"] = {
        " | ".join(k): v for k, v in sorted(counts.items())
    }
    for model in sorted({r["model"] for r in drows}):
        for language in sorted({r["language"] for r in drows}):
            items = [len(r.get("full_response", "")) for r in drows if r["model"] == model and r["language"] == language]
            out["deliberative_length_diagnostic"]["response_chars_by_model_language"][f"{model} | {language}"] = describe_lengths(items)

    # Language raw and valid-conditional correctness in clean factorial.
    lang: dict[str, Any] = {}
    for interface in ("direct", "deliberative"):
        lang[interface] = {}
        for language in sorted({r["language"] for r in rows}):
            sub = [r for r in rows if r["interface"] == interface and r["language"] == language]
            valid = [r for r in sub if b(r["valid"])]
            raw_correct = sum(b(r["command_correct"]) for r in sub)
            valid_correct = sum(b(r["command_correct"]) for r in valid)
            lang[interface][language] = {
                "n": len(sub), "correct": raw_correct, "accuracy": raw_correct/len(sub),
                "valid": len(valid), "correct_given_valid": valid_correct,
                "accuracy_given_valid": valid_correct/len(valid) if valid else None,
                "extraction_errors": sum(bool(r.get("final_extraction_error")) for r in sub),
            }
    out["language"] = lang

    json_path = HERE / "controls" / "SYMMETRIC-FACTORIAL-MECHANISM-AUDIT.json"
    md_path = HERE / "controls" / "SYMMETRIC-FACTORIAL-MECHANISM-AUDIT.md"
    json_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = ["# Symmetric factorial mechanism audit", "", f"Run: `{run}`", ""]
    lines += ["## Truth × first-position split", "", "| Interface | Oracle first | Oracle second | First selected | Position-only null |", "|---|---:|---:|---:|---:|"]
    for interface, s in truth_split.items():
        a, z = s["oracle_is_first"], s["oracle_is_second"]
        lines.append(
            f"| {interface} | {a['correct']}/{a['n']} ({100*a['accuracy']:.1f}%) | "
            f"{z['correct']}/{z['n']} ({100*z['accuracy']:.1f}%) | "
            f"{s['first_position_selected']}/{a['n']+z['n']} ({100*s['first_position_selected_rate']:.1f}%) | 50.0% |"
        )
    lines += ["", "Wilson 95% intervals:"]
    for interface, s in truth_split.items():
        for label in ("oracle_is_first", "oracle_is_second"):
            x=s[label]; lo,hi=x["wilson95"]
            lines.append(f"- {interface} / {label}: {100*x['accuracy']:.1f}% [{100*lo:.1f}, {100*hi:.1f}].")

    dl = out["deliberative_length_diagnostic"]
    lines += ["", "## Deliberative extraction/length diagnostic", "",
              f"- failed extraction: {dl['failed_extraction']}",
              f"- successful extraction: {dl['successful_extraction']}", "",
              "Failures by model/language/order:"]
    for k,v in dl["failure_by_model_language_order"].items(): lines.append(f"- {k}: {v}")
    lines += ["", "Response characters by model/language:"]
    for k,v in dl["response_chars_by_model_language"].items(): lines.append(f"- {k}: {v}")
    lines += ["", "Failure suffixes (diagnostic only):"]
    for suffix in dl["failed_response_suffixes"]: lines.append(f"- `{suffix.replace(chr(10), '↵')}`")

    lines += ["", "## Language correctness", ""]
    for interface, langs in lang.items():
        for language, s in langs.items():
            lines.append(
                f"- {interface} / {language}: raw {s['correct']}/{s['n']} ({100*s['accuracy']:.1f}%); "
                f"given valid {s['correct_given_valid']}/{s['valid']} ({100*s['accuracy_given_valid']:.1f}%); "
                f"extraction errors {s['extraction_errors']}."
            )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(md_path)
    print(json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
