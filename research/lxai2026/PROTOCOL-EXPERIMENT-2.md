# LXAI 2026 Experiment 2: decision complexity × Spanish variety

This protocol defines the follow-up experiment before any Experiment 2 model calls are collected. Experiment 1 and its stored main-run results remain unchanged.

## Research question

Does the difference in executable-action fidelity between broadly standardised written Spanish and voseo-marked Rioplatense Spanish change as selecting the action requires progressively more computation over game state?

The experiment does not claim novelty for stateful tool use, state-dependent reasoning, or deterministic evaluation. Those are established in prior work including ToolSandbox and BFCL. The narrower object is the interaction between within-Spanish regional variation and controlled executable decision complexity.

## Design

The suite contains 48 cases: 12 decision policies, each instantiated in four counterbalanced game states. Each policy therefore maps the same linguistic instruction to different correct commands depending on state. This prevents success from being explained by a fixed association between an instruction and one command.

Each case has three semantically matched language conditions:

1. English (`en`), retained as a secondary reference;
2. broadly standardised written Spanish (`es_standard`);
3. voseo-marked Rioplatense Spanish (`es_rioplatense`).

The primary inferential comparison is standardised Spanish versus Rioplatense Spanish.

## Decision-complexity levels

There are eight cases at each level, comprising two policies with four state variants each.

- **D1 — single-state predicate:** one state field and one conditional threshold/status check.
- **D2 — relational comparison:** comparison between own and opponent state.
- **D3 — Boolean composition:** conjunction or exclusive-or across multiple state facts.
- **D4 — ordered/nested policy:** precedence among multiple conditional branches.
- **D5 — derived numerical state:** arithmetic or distance must be computed from state before selecting an action.
- **D6 — composite policy:** derived or relational state is combined with nested/ordered multi-variable decisions.

The levels are an experimental manipulation of decision structure, not a claim of a universal psychological or computational complexity scale.

## Counter-state requirement

Every policy is evaluated in four state variants and must yield at least two distinct correct commands across those states. The instruction wording is held constant within a language condition across the four states. A model therefore has to use the supplied game state to obtain all variants correctly.

## Models and invocation

Use the same four local model conditions as Experiment 1:

- `mistral-small3.2:24b-instruct-2506-q4_K_M`
- `qwen3:30b-a3b-instruct-2507-q4_K_M`
- `qwen3:4b-instruct-2507-q4_K_M`
- `llama3.2:latest`

Use the same stateless system prompt, BatLLM command grammar, temperature (`0.0`), seed (`20260825`), output-token limit (`24`), strict parser, deterministic execution semantics, and condition randomisation procedure as Experiment 1.

Total main-run calls: 48 cases × 3 language conditions × 4 models = **576 calls**.

## Outcomes

The primary outcome remains **strict command correctness** under BatLLM's unchanged production parser.

Primary reporting:

- strict accuracy for standardised Spanish and Rioplatense Spanish at D1–D6;
- paired standard-minus-Rioplatense difference at each level;
- discordant-pair counts and exact McNemar result at each level;
- the trajectory of the paired language difference as decision level increases.

Secondary outcomes:

- strict command validity;
- action-family correctness;
- parameter correctness where applicable;
- deterministic executable-consequence correctness;
- per-model results;
- per-policy counter-state consistency.

A formal language-condition × decision-level interaction analysis may supplement the paired results, but no post-hoc redefinition of the D1–D6 levels is permitted after seeing model outputs.

## Interpretation constraints

A decline shared by both Spanish conditions as D1–D6 increases is evidence about decision difficulty in this bounded task, not dialect disadvantage.

A Spanish-variety effect is supported only by a difference between the matched Spanish conditions, especially if that difference changes systematically with decision level. English is contextual rather than the primary inferential baseline.

Nonsignificant differences do not establish equivalence unless an equivalence margin is defined separately and prospectively.

Claims remain limited to the constructions represented here. The Rioplatense condition primarily manipulates voseo morphology and closely matched phrasing rather than the full lexical, pragmatic, social, or geographic breadth of Rioplatense Spanish.

## Freeze rule

Before the first Experiment 2 model call, perform a final language/logic review and a dry run. After the main Experiment 2 run begins, do not alter prompts, expected actions, policy definitions, states, scoring rules, model set, or decision-level assignments for the reported main analysis. Any later changes constitute a separate robustness experiment.