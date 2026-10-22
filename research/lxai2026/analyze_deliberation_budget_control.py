"""Compare the 1024-token deliberation budget control with the original 256-token arm."""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def latest_child(path: Path) -> Path | None:
    children = sorted((p for p in path.iterdir() if p.is_dir()), key=lambda p: p.name) if path.exists() else []
    return children[-1] if children else None


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def b(v: str) -> bool:
    return v == "True"


def describe(items: list[dict[str, str]]) -> dict[str, Any]:
    valid = [r for r in items if b(r["valid"])]
    lengths = [len(r.get("full_response", "")) for r in items]
    eval_counts = [
        int(float(r["ollama_eval_count"]))
        for r in items
        if r.get("ollama_eval_count") not in (None, "", "None")
    ]
    from collections import Counter
    return {
        "n": len(items),
        "correct": sum(b(r["command_correct"]) for r in items),
        "valid": len(valid),
        "correct_given_valid": sum(b(r["command_correct"]) for r in valid),
        "extraction_errors": sum(bool(r.get("final_extraction_error")) for r in items),
        "mean_chars": statistics.fmean(lengths) if lengths else None,
        "median_chars": statistics.median(lengths) if lengths else None,
        "mean_eval_count": statistics.fmean(eval_counts) if eval_counts else None,
        "max_eval_count": max(eval_counts) if eval_counts else None,
        "done_reasons": dict(sorted(Counter(r.get("ollama_done_reason", "") for r in items).items())),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--original", type=Path)
    p.add_argument("--budget", type=Path)
    args = p.parse_args(argv)
    original = args.original or latest_child(HERE / "controls" / "symmetric_clause_factorial")
    budget = args.budget or latest_child(HERE / "controls" / "deliberation_budget")
    if not original or not budget:
        raise SystemExit("Missing original or budget-control run")

    old = [r for r in read_rows(original / "results.csv") if r["interface"] == "deliberative"]
    new = read_rows(budget / "results.csv")
    old_index = {
        (r["model"], r["language"], r["order"], r["case_id"], r["repeat"]): r
        for r in old
    }
    pairs: list[tuple[dict[str, str], dict[str, str]]] = []
    for r in new:
        k = (r["model"], r["language"], r["order"], r["case_id"], r["repeat"])
        pairs.append((old_index[k], r))

    old_fail_pairs = [(a, c) for a, c in pairs if bool(a.get("final_extraction_error"))]
    old_success_pairs = [(a, c) for a, c in pairs if not bool(a.get("final_extraction_error"))]

    out: dict[str, Any] = {
        "original": str(original),
        "budget": str(budget),
        "n_pairs": len(pairs),
        "by_model_language": {},
        "overall": {},
    }
    for label, rows in (("original_256", old), ("budget_1024", new)):
        out["overall"][label] = describe(rows)

    for model in sorted({r["model"] for r in new}):
        out["by_model_language"][model] = {}
        for lang in sorted({r["language"] for r in new}):
            o = [a for a, c in pairs if c["model"] == model and c["language"] == lang]
            n = [c for a, c in pairs if c["model"] == model and c["language"] == lang]
            out["by_model_language"][model][lang] = {
                "original_256": describe(o),
                "budget_1024": describe(n),
            }

    out["paired"] = {
        "old_wrong_new_correct": sum((not b(a["command_correct"])) and b(c["command_correct"]) for a, c in pairs),
        "old_correct_new_wrong": sum(b(a["command_correct"]) and (not b(c["command_correct"])) for a, c in pairs),
        "old_extraction_failure_new_valid": sum(b(c["valid"]) for a, c in old_fail_pairs),
        "old_extraction_failure_new_correct": sum(b(c["command_correct"]) for a, c in old_fail_pairs),
        "old_failure_exact_prefix_of_new": sum(c.get("full_response", "").startswith(a.get("full_response", "")) for a, c in old_fail_pairs),
        "old_success_exact_response_unchanged": sum(a.get("full_response", "") == c.get("full_response", "") for a, c in old_success_pairs),
        "old_success_final_command_unchanged": sum(a.get("normalized_command", "") == c.get("normalized_command", "") for a, c in old_success_pairs),
        "n_old_extraction_failures": len(old_fail_pairs),
        "n_old_successes": len(old_success_pairs),
    }

    out["old_failure_followup"] = [
        {
            "model": c["model"],
            "language": c["language"],
            "order": c["order"],
            "case_id": c["case_id"],
            "old_chars": len(a.get("full_response", "")),
            "new_chars": len(c.get("full_response", "")),
            "old_is_exact_prefix": c.get("full_response", "").startswith(a.get("full_response", "")),
            "new_correct": b(c["command_correct"]),
            "new_valid": b(c["valid"]),
            "new_done_reason": c.get("ollama_done_reason"),
            "new_eval_count": c.get("ollama_eval_count"),
        }
        for a, c in old_fail_pairs
    ]

    json_path = HERE / "controls" / "DELIBERATION-BUDGET-CONTROL.json"
    md_path = HERE / "controls" / "DELIBERATION-BUDGET-CONTROL.md"
    json_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    lines = [
        "# Deliberation output-budget control",
        "",
        f"Original: `{original}`",
        f"Budget control: `{budget}`",
        "",
        "## Overall",
        "",
    ]
    for label, s in out["overall"].items():
        raw = 100 * s["correct"] / s["n"]
        cond = 100 * s["correct_given_valid"] / s["valid"] if s["valid"] else 0
        lines.append(
            f"- {label}: correct {s['correct']}/{s['n']} ({raw:.1f}%); valid {s['valid']}/{s['n']}; "
            f"correct|valid {s['correct_given_valid']}/{s['valid']} ({cond:.1f}%); extraction errors "
            f"{s['extraction_errors']}; mean chars {s['mean_chars']:.1f}; median chars {s['median_chars']:.1f}; "
            f"done reasons {s['done_reasons']}."
        )

    lines += ["", "## By model and language", ""]
    for model, langs in out["by_model_language"].items():
        for lang, cells in langs.items():
            a = cells["original_256"]
            c = cells["budget_1024"]
            lines.append(
                f"- {model} / {lang}: 256={a['correct']}/{a['n']} correct, {a['extraction_errors']} extraction errors, "
                f"mean chars {a['mean_chars']:.1f}; 1024={c['correct']}/{c['n']} correct, {c['extraction_errors']} "
                f"extraction errors, mean chars {c['mean_chars']:.1f}, done reasons {c['done_reasons']}, "
                f"max eval_count {c['max_eval_count']}."
            )

    lines += ["", "## Paired repair and prefix test", ""]
    for k, v in out["paired"].items():
        lines.append(f"- {k}: {v}")
    lines += ["", "Old extraction failures under the 1024-token rerun:", ""]
    for item in out["old_failure_followup"]:
        lines.append(
            f"- {item['model']} / {item['language']} / {item['order']} / {item['case_id']}: "
            f"chars {item['old_chars']} -> {item['new_chars']}; prefix={item['old_is_exact_prefix']}; "
            f"new_correct={item['new_correct']}; done_reason={item['new_done_reason']}; eval_count={item['new_eval_count']}."
        )

    md_path.write_text("\n".join(lines) + "\n")
    print(md_path)
    print(json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
