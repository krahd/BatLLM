"""Analyse the LXAI 2026 format-only control against direct and deliberative factorial arms."""
from __future__ import annotations

import argparse
import csv
import json
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
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def b(v: str) -> bool:
    return v == "True"


def pct(n: int, d: int) -> float:
    return 100.0 * n / d if d else 0.0


def summarize(rows: list[dict[str, str]]) -> dict[str, Any]:
    valid = [r for r in rows if b(r["valid"])]
    return {
        "n": len(rows),
        "correct": sum(b(r["command_correct"]) for r in rows),
        "valid": len(valid),
        "correct_given_valid": sum(b(r["command_correct"]) for r in valid),
        "first_position": sum(b(r["selected_first_position"]) for r in rows),
        "extraction_errors": sum(bool(r.get("final_extraction_error")) for r in rows),
        "provider_errors": sum(bool(r.get("provider_error")) for r in rows),
    }


def truth_position(rows: list[dict[str, str]]) -> dict[str, Any]:
    first_oracle = [r for r in rows if r["expected_command"] == r["first_position_command"]]
    second_oracle = [r for r in rows if r["expected_command"] == r["second_position_command"]]
    return {
        "oracle_first_n": len(first_oracle),
        "oracle_first_correct": sum(b(r["command_correct"]) for r in first_oracle),
        "oracle_second_n": len(second_oracle),
        "oracle_second_correct": sum(b(r["command_correct"]) for r in second_oracle),
    }


def order_pairs(rows: list[dict[str, str]]) -> dict[str, Any]:
    idx: dict[tuple[str, str, str, str], dict[str, dict[str, str]]] = defaultdict(dict)
    for r in rows:
        key = (r["model"], r["language"], r["case_id"], r["repeat"])
        idx[key][r["order"]] = r
    pairs = 0
    changed = 0
    correct_both = 0
    follows_first_both = 0
    for pair in idx.values():
        if "a_first" not in pair or "b_first" not in pair:
            continue
        a, z = pair["a_first"], pair["b_first"]
        pairs += 1
        changed += int(a["normalized_command"] != z["normalized_command"])
        correct_both += int(b(a["command_correct"]) and b(z["command_correct"]))
        follows_first_both += int(b(a["selected_first_position"]) and b(z["selected_first_position"]))
    return {
        "pairs": pairs,
        "output_changed": changed,
        "correct_both": correct_both,
        "follows_first_in_both": follows_first_both,
    }


def policy_groups(rows: list[dict[str, str]]) -> dict[str, Any]:
    groups: dict[tuple[str, str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        groups[(r["model"], r["language"], r["order"], r["policy_id"], r["repeat"])].append(r)
    complete = invariant = 0
    for items in groups.values():
        complete += int(all(b(r["command_correct"]) for r in items))
        expected = {r["expected_command"] for r in items}
        outputs = {r["normalized_command"] for r in items}
        invariant += int(len(expected) > 1 and len(outputs) == 1)
    return {"groups": len(groups), "complete": complete, "state_invariant": invariant}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--format-run", type=Path)
    p.add_argument("--factorial-run", type=Path)
    args = p.parse_args(argv)
    fmt_dir = args.format_run or latest_child(HERE / "controls" / "format_only")
    fac_dir = args.factorial_run or latest_child(HERE / "controls" / "symmetric_clause_factorial")
    if fmt_dir is None or fac_dir is None:
        raise SystemExit("Missing format-only or factorial run")
    fmt = read_rows(fmt_dir / "results.csv")
    factorial = read_rows(fac_dir / "results.csv")
    arms = {
        "direct": [r for r in factorial if r["interface"] == "direct"],
        "format_only": fmt,
        "deliberative_256": [r for r in factorial if r["interface"] == "deliberative"],
    }
    out: dict[str, Any] = {"format_run": str(fmt_dir), "factorial_run": str(fac_dir), "arms": {}}
    for name, rows in arms.items():
        out["arms"][name] = {
            "summary": summarize(rows),
            "truth_position": truth_position(rows),
            "order_pairs": order_pairs(rows),
            "policy_groups": policy_groups(rows),
        }
    out["by_model_language"] = {}
    for name, rows in arms.items():
        out["by_model_language"][name] = {}
        for model in sorted({r["model"] for r in rows}):
            out["by_model_language"][name][model] = {}
            for language in sorted({r["language"] for r in rows}):
                subset = [r for r in rows if r["model"] == model and r["language"] == language]
                out["by_model_language"][name][model][language] = summarize(subset)

    json_path = HERE / "controls" / "FORMAT-ONLY-CONTROL.json"
    md_path = HERE / "controls" / "FORMAT-ONLY-CONTROL.md"
    json_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Format-only control",
        "",
        f"Format-only run: `{fmt_dir}`",
        f"Reference factorial: `{fac_dir}`",
        "",
        "The format-only arm requires exactly `FINAL: <command>` but explicitly forbids intermediate reasoning. It therefore tests whether the deliberative rescue is attributable merely to the final-output convention rather than permission for intermediate computation.",
        "",
        "## Pooled comparison",
        "",
        "| Arm | Correct | Valid | First-position | Oracle-first correct | Oracle-second correct | Output changed across order swap | Correct both orders | Follows first in both orders | Policy-complete | State-invariant |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ("direct", "format_only", "deliberative_256"):
        x = out["arms"][name]
        s, t, o, g = x["summary"], x["truth_position"], x["order_pairs"], x["policy_groups"]
        lines.append(
            f"| {name} | {s['correct']}/{s['n']} ({pct(s['correct'], s['n']):.1f}%) | "
            f"{s['valid']}/{s['n']} ({pct(s['valid'], s['n']):.1f}%) | "
            f"{s['first_position']}/{s['n']} ({pct(s['first_position'], s['n']):.1f}%) | "
            f"{t['oracle_first_correct']}/{t['oracle_first_n']} ({pct(t['oracle_first_correct'], t['oracle_first_n']):.1f}%) | "
            f"{t['oracle_second_correct']}/{t['oracle_second_n']} ({pct(t['oracle_second_correct'], t['oracle_second_n']):.1f}%) | "
            f"{o['output_changed']}/{o['pairs']} ({pct(o['output_changed'], o['pairs']):.1f}%) | "
            f"{o['correct_both']}/{o['pairs']} ({pct(o['correct_both'], o['pairs']):.1f}%) | "
            f"{o['follows_first_in_both']}/{o['pairs']} ({pct(o['follows_first_in_both'], o['pairs']):.1f}%) | "
            f"{g['complete']}/{g['groups']} ({pct(g['complete'], g['groups']):.1f}%) | "
            f"{g['state_invariant']}/{g['groups']} ({pct(g['state_invariant'], g['groups']):.1f}%) |"
        )
    lines += ["", "## By model and language", ""]
    for name, models in out["by_model_language"].items():
        lines.append(f"### {name}")
        for model, langs in models.items():
            for language, s in langs.items():
                lines.append(
                    f"- {model} / {language}: {s['correct']}/{s['n']} correct; {s['valid']}/{s['n']} valid; "
                    f"{s['first_position']}/{s['n']} first-position; extraction errors {s['extraction_errors']}."
                )
        lines.append("")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(md_path)
    print(json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
