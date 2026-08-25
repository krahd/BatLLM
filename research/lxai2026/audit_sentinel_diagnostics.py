"""Sentinel-aware audit for the final LXAI 2026 submission.

No model calls. This script isolates extraction-failure sentinels from
behavioural command diagnostics in the 256-token deliberative arm and checks
that the 1024-token budget control repairs only those protocol failures.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import json
import statistics

HERE = Path(__file__).resolve().parent
SYMMETRIC = HERE / "controls" / "symmetric_clause_factorial" / "20260825T165129Z" / "results.jsonl"
BUDGET = HERE / "controls" / "deliberation_budget" / "20260825T185106Z" / "results.jsonl"
QWEN = "qwen3:30b-a3b-instruct-2507-q4_K_M"


def load(path: Path):
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def norm(value):
    return "" if value is None else str(value)


def failed(row):
    return bool(row.get("final_extraction_error"))


def pair_changed(pair):
    assert len(pair) == 2
    a, b = sorted(pair, key=lambda row: row["order"])
    return norm(a.get("normalized_command")) != norm(b.get("normalized_command"))


def group_complete(group):
    return all(bool(row.get("command_correct")) for row in group)


def group_invariant(group):
    return len({norm(row.get("normalized_command")) for row in group}) == 1


def main():
    symmetric = load(SYMMETRIC)
    old = [row for row in symmetric if row.get("interface") == "deliberative"]
    new = load(BUDGET)
    assert len(old) == len(new) == 256

    old_failed = [row for row in old if failed(row)]
    assert len(old_failed) == 15
    sentinels = {norm(row.get("normalized_command")) for row in old_failed}
    assert sentinels == {"ERR"}, sentinels

    pair_key = lambda row: (row["model"], row["language"], row["case_id"])
    old_pairs = defaultdict(list)
    new_pairs = defaultdict(list)
    for row in old:
        old_pairs[pair_key(row)].append(row)
    for row in new:
        new_pairs[pair_key(row)].append(row)
    assert old_pairs.keys() == new_pairs.keys()
    assert len(old_pairs) == 128

    raw_old_changed = {key for key, pair in old_pairs.items() if pair_changed(pair)}
    raw_new_changed = {key for key, pair in new_pairs.items() if pair_changed(pair)}
    clean_old_pairs = {
        key: pair for key, pair in old_pairs.items()
        if not any(failed(row) for row in pair)
    }
    one_sided = {
        key: pair for key, pair in old_pairs.items()
        if sum(failed(row) for row in pair) == 1
    }
    two_sided = {
        key: pair for key, pair in old_pairs.items()
        if sum(failed(row) for row in pair) == 2
    }
    clean_old_changed = {
        key for key, pair in clean_old_pairs.items() if pair_changed(pair)
    }
    one_sided_raw_changes = {
        key for key, pair in one_sided.items() if pair_changed(pair)
    }

    print("Sentinel-aware deliberative order diagnostics")
    print(f"  256 raw changed pairs: {len(raw_old_changed)}/128")
    print(f"  pairs extractable in both orders: {len(clean_old_pairs)}/128")
    print(f"  behavioural command changes: {len(clean_old_changed)}/{len(clean_old_pairs)}")
    print(f"  one-sided truncation pairs: {len(one_sided)}")
    print(f"  one-sided truncations counted as raw changes: {len(one_sided_raw_changes)}")
    print(f"  two-sided truncation pairs: {len(two_sided)}")
    print(f"  1024 changed pairs: {len(raw_new_changed)}/128")
    print(f"  same behavioural changed-pair identities after repair: {clean_old_changed == raw_new_changed}")

    assert len(raw_old_changed) == 16
    assert len(clean_old_pairs) == 114
    assert len(clean_old_changed) == 3
    assert len(one_sided) == 13
    assert len(one_sided_raw_changes) == 13
    assert len(two_sided) == 1
    assert len(raw_new_changed) == 3
    assert clean_old_changed == raw_new_changed

    group_key = lambda row: (row["model"], row["language"], row["order"], row["policy_id"])
    old_groups = defaultdict(list)
    new_groups = defaultdict(list)
    for row in old:
        old_groups[group_key(row)].append(row)
    for row in new:
        new_groups[group_key(row)].append(row)
    assert old_groups.keys() == new_groups.keys()
    assert len(old_groups) == 64

    raw_old_invariant = {key for key, group in old_groups.items() if group_invariant(group)}
    extractable_old_invariant = {
        key for key, group in old_groups.items()
        if all(not failed(row) for row in group) and group_invariant(group)
    }
    all_failed_invariant = {
        key for key, group in old_groups.items()
        if all(failed(row) for row in group) and group_invariant(group)
    }
    new_invariant = {key for key, group in new_groups.items() if group_invariant(group)}
    newly_complete = {
        key for key in old_groups
        if not group_complete(old_groups[key]) and group_complete(new_groups[key])
    }
    lost_complete = {
        key for key in old_groups
        if group_complete(old_groups[key]) and not group_complete(new_groups[key])
    }

    print("\nSentinel-aware deliberative group diagnostics")
    print(f"  raw 256 state-invariant groups: {len(raw_old_invariant)}/64")
    print(f"  fully extractable 256 state-invariant groups: {len(extractable_old_invariant)}")
    print(f"  all-truncated groups represented as invariant ERR: {len(all_failed_invariant)}")
    print(f"  1024 state-invariant groups: {len(new_invariant)}/64")
    print(f"  newly policy-complete at 1024: {len(newly_complete)}")
    print(f"  newly complete groups containing 256 truncation: {sum(any(failed(row) for row in old_groups[key]) for key in newly_complete)}/{len(newly_complete)}")

    assert len(raw_old_invariant) == 1
    assert not extractable_old_invariant
    assert len(all_failed_invariant) == 1
    only = next(iter(all_failed_invariant))
    assert only[1:] == ("es_rioplatense", "b_first", "D5-P1"), only
    assert not new_invariant
    assert len(newly_complete) == 7
    assert not lost_complete
    assert all(any(failed(row) for row in old_groups[key]) for key in newly_complete)

    # Also expose the full Qwen30 token distributions for an optional plot.
    q_tuteo = [row for row in new if row["model"] == QWEN and row["language"] == "es_standard"]
    q_voseo = [row for row in new if row["model"] == QWEN and row["language"] == "es_rioplatense"]
    ttokens = sorted(int(row["ollama_eval_count"]) for row in q_tuteo)
    vtokens = sorted(int(row["ollama_eval_count"]) for row in q_voseo)
    assert len(ttokens) == len(vtokens) == 64

    print("\nQwen30 full 1024-run generated-token distributions")
    print(f"  tuteo mean={statistics.mean(ttokens):.1f}, max={max(ttokens)}")
    print(f"  voseo mean={statistics.mean(vtokens):.1f}, max={max(vtokens)}")
    print(f"  tuteo sorted: {ttokens}")
    print(f"  voseo sorted: {vtokens}")
    assert round(statistics.mean(ttokens), 1) == 119.9
    assert round(statistics.mean(vtokens), 1) == 165.6
    assert max(ttokens) == 271
    assert max(vtokens) == 600

    print("\nSENTINEL-AWARE FINAL AUDIT: PASS")


if __name__ == "__main__":
    main()
