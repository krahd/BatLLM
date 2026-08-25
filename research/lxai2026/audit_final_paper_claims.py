"""Recompute final LXAI paper claims from committed result artefacts only.

No model calls. This script is a submission preflight: it loads the canonical
symmetric factorial, format-only, 1024-budget, and original deliberation JSONL
files and recomputes the quantities promoted into the final paper.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import json
import math
import statistics

HERE = Path(__file__).resolve().parent

SYMMETRIC = HERE / "controls" / "symmetric_clause_factorial" / "20260825T165129Z" / "results.jsonl"
FORMAT = HERE / "controls" / "format_only" / "20260825T194809Z" / "results.jsonl"
BUDGET = HERE / "controls" / "deliberation_budget" / "20260825T185106Z" / "results.jsonl"
OLD_DELIB = HERE / "controls" / "deliberation" / "20260825T153148Z" / "results.jsonl"


def load(path: Path):
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def norm(v):
    return "" if v is None else str(v)


def metrics(rows):
    n = len(rows)
    correct = sum(bool(r.get("command_correct")) for r in rows)
    valid = sum(bool(r.get("valid")) for r in rows)

    oracle_first = [r for r in rows if norm(r.get("expected_command")) == norm(r.get("first_position_command"))]
    oracle_second = [r for r in rows if norm(r.get("expected_command")) == norm(r.get("second_position_command"))]

    by_pair = defaultdict(list)
    for r in rows:
        key = (r["model"], r["language"], r["case_id"])
        by_pair[key].append(r)
    assert len(by_pair) == 128 and all(len(v) == 2 for v in by_pair.values())
    changed = 0
    correct_both = 0
    follows_first_both = 0
    for pair in by_pair.values():
        a, b = sorted(pair, key=lambda r: r["order"])
        if norm(a.get("normalized_command")) != norm(b.get("normalized_command")):
            changed += 1
        if all(bool(r.get("command_correct")) for r in pair):
            correct_both += 1
        if all(bool(r.get("selected_first_position")) for r in pair):
            follows_first_both += 1

    groups = defaultdict(list)
    for r in rows:
        key = (r["model"], r["language"], r["order"], r["policy_id"])
        groups[key].append(r)
    assert len(groups) == 64 and all(len(v) == 4 for v in groups.values())
    complete = sum(all(bool(r.get("command_correct")) for r in g) for g in groups.values())
    invariant = sum(len({norm(r.get("normalized_command")) for r in g}) == 1 for g in groups.values())

    return {
        "n": n,
        "correct": correct,
        "valid": valid,
        "oracle_first_n": len(oracle_first),
        "oracle_first_correct": sum(bool(r.get("command_correct")) for r in oracle_first),
        "oracle_second_n": len(oracle_second),
        "oracle_second_correct": sum(bool(r.get("command_correct")) for r in oracle_second),
        "order_pairs": len(by_pair),
        "order_changed": changed,
        "correct_both": correct_both,
        "follows_first_both": follows_first_both,
        "groups": len(groups),
        "complete": complete,
        "invariant": invariant,
    }


def pct(k, n):
    return 100.0 * k / n


def print_arm(name, m):
    print(f"\n{name}")
    print(f"  overall: {m['correct']}/{m['n']} = {pct(m['correct'],m['n']):.1f}%")
    print(f"  truth first: {m['oracle_first_correct']}/{m['oracle_first_n']} = {pct(m['oracle_first_correct'],m['oracle_first_n']):.1f}%")
    print(f"  truth second: {m['oracle_second_correct']}/{m['oracle_second_n']} = {pct(m['oracle_second_correct'],m['oracle_second_n']):.1f}%")
    print(f"  gap pp: {pct(m['oracle_first_correct'],m['oracle_first_n'])-pct(m['oracle_second_correct'],m['oracle_second_n']):.1f}")
    print(f"  order changed: {m['order_changed']}/{m['order_pairs']}")
    print(f"  correct both: {m['correct_both']}/{m['order_pairs']}")
    print(f"  follows first both: {m['follows_first_both']}/{m['order_pairs']}")
    print(f"  policy complete: {m['complete']}/{m['groups']}")
    print(f"  state invariant: {m['invariant']}/{m['groups']}")


def token_position(rows):
    # For every command appearing in either clause, compute P(select token | token in position).
    d = defaultdict(lambda: {"first_n":0,"first_selected":0,"second_n":0,"second_selected":0})
    for r in rows:
        first = norm(r["first_position_command"])
        second = norm(r["second_position_command"])
        out = norm(r["normalized_command"])
        d[first]["first_n"] += 1
        d[first]["first_selected"] += int(out == first)
        d[second]["second_n"] += 1
        d[second]["second_selected"] += int(out == second)
    return d


def nearest_rank_p99(vals):
    vals = sorted(vals)
    return vals[math.ceil(0.99 * len(vals)) - 1]


def main():
    symmetric = load(SYMMETRIC)
    direct = [r for r in symmetric if r.get("interface") == "direct"]
    delib256 = [r for r in symmetric if r.get("interface") == "deliberative"]
    format_only = load(FORMAT)
    delib1024 = load(BUDGET)

    arms = {
        "direct": metrics(direct),
        "format_only": metrics(format_only),
        "deliberative_256": metrics(delib256),
        "deliberative_1024": metrics(delib1024),
    }
    for name, m in arms.items():
        print_arm(name, m)

    # Submission-critical assertions.
    expected = {
        "direct": (135,116,19,98,3,51),
        "format_only": (130,99,31,83,3,40),
        "deliberative_256": (238,120,118,16,54,1),
        "deliberative_1024": (253,128,125,3,61,0),
    }
    for name, vals in expected.items():
        m = arms[name]
        got = (m["correct"],m["oracle_first_correct"],m["oracle_second_correct"],m["order_changed"],m["complete"],m["invariant"])
        assert got == vals, f"{name}: expected {vals}, got {got}"

    print("\nDirect token-position diagnostic")
    td = token_position(direct)
    for token in sorted(td):
        x = td[token]
        pf = x["first_selected"] / x["first_n"]
        ps = x["second_selected"] / x["second_n"]
        print(f"  {token:5s}: first {x['first_selected']}/{x['first_n']}={pf:.3f}; second {x['second_selected']}/{x['second_n']}={ps:.3f}")
        assert pf > ps, f"Token {token} does not show the claimed positional direction"

    old = load(OLD_DELIB)
    failed = [r for r in old if r.get("final_extraction_error")]
    ok = [r for r in old if not r.get("final_extraction_error") and not r.get("provider_error")]
    fchars = [int(r.get("response_chars", len(r.get("full_response", "")))) for r in failed]
    ochars = [int(r.get("response_chars", len(r.get("full_response", "")))) for r in ok]
    print("\nOriginal 48-case deliberation extraction diagnostic")
    print(f"  extraction failures: {len(failed)}")
    print(f"  failed mean chars: {statistics.mean(fchars):.1f}; median {statistics.median(fchars):.1f}; min {min(fchars)}; max {max(fchars)}")
    print(f"  success mean chars: {statistics.mean(ochars):.1f}; median {statistics.median(ochars):.1f}; p99 nearest-rank {nearest_rank_p99(ochars)}")
    assert len(failed) == 4

    print("\nFINAL PAPER CLAIM AUDIT: PASS")


if __name__ == "__main__":
    main()
