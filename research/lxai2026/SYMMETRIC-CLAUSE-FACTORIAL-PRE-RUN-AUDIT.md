# Symmetric clause-order factorial — pre-run audit

**Date:** 25 August 2026  
**Runner:** `run_symmetric_clause_order_factorial.py`  
**Status:** ready for post-freeze execution after the currently running continuity control

## Purpose

The earlier branch-reversal control strongly redirected outputs toward the newly first-mentioned action, but its policy rewrites also complemented/rephrased predicates. This clean full-paper control removes that ambiguity by constructing both order conditions from the **same stored pair of explicit policy clauses** and swapping only their order.

The frozen 576-call dataset remains unchanged. This is a separate post-freeze control.

## Mechanical order guarantee

For each `policy_id × language`, the runner stores:

- optional shared `prefix`;
- clause `a`;
- clause `b`.

It renders:

- `a_first = prefix + a + b`
- `b_first = prefix + b + a`

No alternate paraphrase exists between order conditions. The literal clause strings are therefore identical across the two conditions; only sentence order changes.

## Policy logic audit

### D1-P1 — shield Boolean

- A: shield raised → `S0`
- B: shield down → `B`

`shield` is Boolean, so raised/down are exhaustive and mutually exclusive.

### D1-P2 — health threshold

- A: health < 15 → `S1`
- B: health ≥ 15 → `M`

Exact complement including the health=15 boundary already present in the frozen suite.

### D2-P1 — health relation

- A: own health < opponent health → `S1`
- B: own health ≥ opponent health → `B`

Exact complement including equality.

### D2-P2 — x-coordinate relation

- A: own x > opponent x → `A90`
- B: own x ≤ opponent x → `C90`

Exact complement including equality.

### D3-P1 — conjunction / complement

- A: health < 15 **and** shield down → `S1`
- B: health ≥ 15 **or** shield raised → `B`

By De Morgan's law and Boolean shield state, B is exactly the complement of A. Importantly, both order conditions contain these same two clauses; unlike the first reversal control, the logical form itself does not change between orders.

### D3-P2 — XOR / equality

- A: exactly one shield raised → `M`
- B: two shields in the same state → `B`

For two Boolean shields, XOR and equality are exhaustive complements.

### D5-P1 — derived health difference

- A: own health is at least 10 points higher → `B`
- B: own health is **not** at least 10 points higher → `S1`

Exact logical complement including the +10 boundary. The wording is intentionally explicit rather than stylistically elegant because the same clause must be used in both orders.

### D5-P2 — derived horizontal distance

Shared prefix in both order conditions: compute horizontal distance.

- A: distance ≥ 0.4 → `M0.1`
- B: distance < 0.4 → `C90`

Exact complement including the distance=0.4 boundary.

## Language audit

The default experiment uses:

- tuteo (`tienes`, `levanta`, `avanza`, `gira`, `calcula`);
- Rioplatense voseo (`tenés`, `levantá`, `avanzá`, `girá`, `calculá`).

The clause-order manipulation itself is identical within each language condition. No tuteo/voseo clause changes between A-first and B-first.

The Spanish forms are intentionally close and technical. They do not claim to represent the broader lexical/pragmatic range of either usage community.

## Interface factor

The exact same clause/order cells are crossed with:

1. **direct** — frozen `DECISION_SYSTEM_PROMPT`, exactly one command token, `num_predict=24`;
2. **deliberative** — explicit scratchpad allowed, strict `FINAL: <command>` extraction, `num_predict=256`.

Transport, temperature, seed logic, game state, parser, oracle and execution semantics are shared.

## Planned default size

With Mistral24 + Qwen30:

32 semantic states × 2 Spanish conditions × 2 clause orders × 2 interfaces × 2 models = **512 calls**.

## Primary analysis

Do **not** make aggregate accuracy the only order measure. The clean paired outcomes are:

- output changes between A-first and B-first for the exact same state;
- correct in both orders;
- follows the first-position action in both orders;
- policy-complete and state-invariant rates by interface/order;
- first-position selection pooled by interface;
- latency and response-length cost of deliberation.

The key interaction is whether direct output is more order-sensitive than deliberative output.

## Interpretation rules before seeing data

1. **Direct order-sensitive; deliberative order-invariant:** strongest interaction story. Direct-command interface exposes positional shortcut; deliberation attenuates it.
2. **Both order-sensitive, deliberative more accurate:** state reasoning is rescued but positional sensitivity survives as a partially independent effect.
3. **Clean direct condition not strongly order-sensitive:** downgrade the first reversal control to formulation sensitivity; centre the paper on interface-conditioned state use rather than position.
4. **Tuteo/voseo differences remain small:** retain language as secondary axis; no equivalence claim.
5. **Large tuteo/voseo interaction appears:** investigate before writing; do not retrofit a dialect story without checking exact cases.

## Pre-run verdict

**PASS.** The new runner fixes the principal causal-identification weakness in the first branch-reversal control. It is suitable as the key clean experiment for the Full Paper expansion.
