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


def response_chars(row):
    v = row.get("response_chars")
    return int(v) if v not in (None, "") else len(row.get("full_response", ""))


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


def nearest_rank(vals, q):
    vals = sorted(vals)
    return vals[math.ceil(q * len(vals)) - 1]


def nearest_rank_p99(vals):
    return nearest_rank(vals, 0.99)


def higher_iqr(vals):
    """Q1/Q3 using the empirical 'higher' quantile convention.

    For a sample of n observations, each quantile is the observed value at
    ceil(q * (n - 1)) in zero-based sorted order. This is the convention used
    for the character-count IQRs reported in the paper.
    """
    vals = sorted(vals)
    n = len(vals)
    return vals[math.ceil(0.25 * (n - 1))], vals[math.ceil(0.75 * (n - 1))]


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
        "direct": (135,116,19,98,91,3,51),
        "format_only": (130,99,31,83,58,3,40),
        "deliberative_256": (238,120,118,16,2,54,1),
        "deliberative_1024": (253,128,125,3,2,61,0),
    }
    for name, vals in expected.items():
        m = arms[name]
        got = (
            m["correct"],
            m["oracle_first_correct"],
            m["oracle_second_correct"],
            m["order_changed"],
            m["follows_first_both"],
            m["complete"],
            m["invariant"],
        )
        assert got == vals, f"{name}: expected {vals}, got {got}"

    print("\nDirect token-position diagnostic")
    td = token_position(direct)
    for token in sorted(td):
        x = td[token]
        pf = x["first_selected"] / x["first_n"]
        ps = x["second_selected"] / x["second_n"]
        print(f"  {token:5s}: first {x['first_selected']}/{x['first_n']}={pf:.3f}; second {x['second_selected']}/{x['second_n']}={ps:.3f}")
        assert pf > ps, f"Token {token} does not show the claimed positional direction"

    # Direct and format-only ceilings are non-binding in the symmetric experiment.
    direct_chars = [response_chars(r) for r in direct]
    format_chars = [response_chars(r) for r in format_only]
    direct_failures = sum(bool(r.get("final_extraction_error")) for r in direct)
    format_failures = sum(bool(r.get("final_extraction_error")) for r in format_only)
    print("\nNon-binding output ceilings")
    print(f"  direct: max chars {max(direct_chars)}; extraction failures {direct_failures}")
    print(f"  format-only: max chars {max(format_chars)}; extraction failures {format_failures}")
    assert max(direct_chars) == 4
    assert max(format_chars) == 11
    assert direct_failures == 0 and format_failures == 0

    # Paired 256 -> 1024 budget repair: every correctness change must be a
    # repaired 256-token extraction failure, with no regression.
    key = lambda r: (r["model"], r["language"], r["order"], r["case_id"])
    old_by_key = {key(r): r for r in delib256}
    new_by_key = {key(r): r for r in delib1024}
    assert old_by_key.keys() == new_by_key.keys()
    improved = []
    regressed = []
    changed_success_commands = []
    prefix_repairs = 0
    unchanged_success_responses = 0
    for k in old_by_key:
        old = old_by_key[k]
        new = new_by_key[k]
        if not old.get("command_correct") and new.get("command_correct"):
            improved.append((old, new))
        if old.get("command_correct") and not new.get("command_correct"):
            regressed.append((old, new))
        if old.get("valid"):
            if norm(old.get("normalized_command")) != norm(new.get("normalized_command")):
                changed_success_commands.append((old, new))
            if old.get("full_response", "") == new.get("full_response", ""):
                unchanged_success_responses += 1
        if old.get("final_extraction_error") and new.get("valid"):
            if new.get("full_response", "").startswith(old.get("full_response", "")):
                prefix_repairs += 1

    print("\nPaired 256 -> 1024 repair")
    print(f"  improved correctness: {len(improved)}")
    print(f"  regressions: {len(regressed)}")
    print(f"  improved rows that were 256-token extraction failures: {sum(bool(o.get('final_extraction_error')) for o,_ in improved)}")
    print(f"  successful final commands changed: {len(changed_success_commands)}")
    print(f"  old successful full responses byte-identical: {unchanged_success_responses}/241")
    print(f"  old failed response exact prefixes: {prefix_repairs}/15")
    assert len(improved) == 15
    assert not regressed
    assert all(bool(o.get("final_extraction_error")) for o, _ in improved)
    assert not changed_success_commands
    assert unchanged_success_responses == 240
    assert prefix_repairs == 14

    # The secondary command-derived diagnostics in the paper must change only
    # in pairs/groups containing a repaired 256-token truncation. This is a
    # stronger check than comparing aggregate counts alone.
    pair_key = lambda r: (r["model"], r["language"], r["case_id"])
    old_pairs = defaultdict(list)
    new_pairs = defaultdict(list)
    for r in delib256:
        old_pairs[pair_key(r)].append(r)
    for r in delib1024:
        new_pairs[pair_key(r)].append(r)
    assert old_pairs.keys() == new_pairs.keys()

    def pair_changed(pair):
        a, b = sorted(pair, key=lambda r: r["order"])
        return norm(a.get("normalized_command")) != norm(b.get("normalized_command"))

    def pair_follows_first(pair):
        return all(bool(r.get("selected_first_position")) for r in pair)

    resolved_swaps = [k for k in old_pairs if pair_changed(old_pairs[k]) and not pair_changed(new_pairs[k])]
    introduced_swaps = [k for k in old_pairs if not pair_changed(old_pairs[k]) and pair_changed(new_pairs[k])]
    pair_metric_changes = [
        k
        for k in old_pairs
        if pair_changed(old_pairs[k]) != pair_changed(new_pairs[k])
        or pair_follows_first(old_pairs[k]) != pair_follows_first(new_pairs[k])
    ]
    assert all(any(bool(r.get("final_extraction_error")) for r in old_pairs[k]) for k in pair_metric_changes)

    group_key = lambda r: (r["model"], r["language"], r["order"], r["policy_id"])
    old_groups = defaultdict(list)
    new_groups = defaultdict(list)
    for r in delib256:
        old_groups[group_key(r)].append(r)
    for r in delib1024:
        new_groups[group_key(r)].append(r)
    assert old_groups.keys() == new_groups.keys()

    def group_complete(group):
        return all(bool(r.get("command_correct")) for r in group)

    def group_invariant(group):
        return len({norm(r.get("normalized_command")) for r in group}) == 1

    group_metric_changes = [
        k
        for k in old_groups
        if group_complete(old_groups[k]) != group_complete(new_groups[k])
        or group_invariant(old_groups[k]) != group_invariant(new_groups[k])
    ]
    assert all(any(bool(r.get("final_extraction_error")) for r in old_groups[k]) for k in group_metric_changes)

    print("\nPost-repair secondary diagnostics")
    print(f"  order changed: {arms['deliberative_256']['order_changed']}/128 -> {arms['deliberative_1024']['order_changed']}/128")
    print(f"  resolved order swaps: {len(resolved_swaps)}; introduced order swaps: {len(introduced_swaps)}")
    print(f"  follows first both: {arms['deliberative_256']['follows_first_both']}/128 -> {arms['deliberative_1024']['follows_first_both']}/128")
    print(f"  policy complete: {arms['deliberative_256']['complete']}/64 -> {arms['deliberative_1024']['complete']}/64")
    print(f"  state invariant: {arms['deliberative_256']['invariant']}/64 -> {arms['deliberative_1024']['invariant']}/64")
    print(f"  changed pair diagnostics touching a 256-token truncation: {len(pair_metric_changes)}/{len(pair_metric_changes)}")
    print(f"  changed group diagnostics touching a 256-token truncation: {len(group_metric_changes)}/{len(group_metric_changes)}")
    assert len(resolved_swaps) == 13
    assert not introduced_swaps

    # Qwen30 language-conditioned response-length distribution at the
    # non-binding 1024-token ceiling. Internal es_standard = tuteo.
    qwen = "qwen3:30b-a3b-instruct-2507-q4_K_M"
    q_tuteo = [r for r in delib1024 if r["model"] == qwen and r["language"] == "es_standard"]
    q_voseo = [r for r in delib1024 if r["model"] == qwen and r["language"] == "es_rioplatense"]
    assert len(q_tuteo) == len(q_voseo) == 64
    tchars = [response_chars(r) for r in q_tuteo]
    vchars = [response_chars(r) for r in q_voseo]
    t_iqr = higher_iqr(tchars)
    v_iqr = higher_iqr(vchars)
    t_med = statistics.median(tchars)
    v_med = statistics.median(vchars)
    lang_key = lambda r: (r["order"], r["case_id"])
    t_by_cell = {lang_key(r): response_chars(r) for r in q_tuteo}
    v_by_cell = {lang_key(r): response_chars(r) for r in q_voseo}
    assert t_by_cell.keys() == v_by_cell.keys()
    voseo_longer = sum(v_by_cell[k] > t_by_cell[k] for k in t_by_cell)

    print("\nQwen30 1024-token response-length distribution")
    print(f"  tuteo: mean {statistics.mean(tchars):.1f}; median {t_med:.1f}; IQR {t_iqr[0]}-{t_iqr[1]}; max {max(tchars)}")
    print(f"  voseo: mean {statistics.mean(vchars):.1f}; median {v_med:.1f}; IQR {v_iqr[0]}-{v_iqr[1]}; max {max(vchars)}")
    print(f"  voseo longer in paired cells: {voseo_longer}/64")
    assert round(statistics.mean(tchars), 1) == 368.8
    assert round(statistics.mean(vchars), 1) == 517.4
    assert t_med == 304 and v_med == 436
    assert t_iqr == (252, 401), t_iqr
    assert v_iqr == (263, 735), v_iqr
    assert max(tchars) == 842 and max(vchars) == 2459
    assert voseo_longer == 39

    old = load(OLD_DELIB)
    failed = [r for r in old if r.get("final_extraction_error")]
    ok = [r for r in old if not r.get("final_extraction_error") and not r.get("provider_error")]
    fchars = [response_chars(r) for r in failed]
    ochars = [response_chars(r) for r in ok]
    print("\nOriginal 48-case deliberation extraction diagnostic")
    print(f"  extraction failures: {len(failed)}")
    print(f"  failed mean chars: {statistics.mean(fchars):.1f}; median {statistics.median(fchars):.1f}; min {min(fchars)}; max {max(fchars)}")
    print(f"  success mean chars: {statistics.mean(ochars):.1f}; median {statistics.median(ochars):.1f}; p99 nearest-rank {nearest_rank_p99(ochars)}")
    assert len(failed) == 4

    print("\nFINAL PAPER CLAIM AUDIT: PASS")


if __name__ == "__main__":
    main()
