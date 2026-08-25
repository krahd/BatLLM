# LXAI 2026 decision complexity × Spanish variety

This protocol defines the main decision-complexity experiment. An earlier baseline run was discarded after a transport audit showed that the Modelito 1.4.5 Ollama adapter did not transmit the nominal generation settings. Its stored results and result-specific interpretation were removed and are not part of the evidence base for this study.

## Research question

Does the difference in executable-action fidelity between broadly standardised written Spanish and voseo-marked Rioplatense Spanish change as selecting the action requires progressively more computation over game state?

The experiment does not claim novelty for stateful tool use, state-dependent reasoning, or deterministic evaluation. Those are established in prior work including ToolSandbox and BFCL. The narrower object is the interaction between within-Spanish regional variation and controlled executable decision structure.

## Design

The suite contains 48 cases: 12 decision policies, each instantiated in four counter-state game states. Each policy therefore maps the same linguistic instruction to different correct commands depending on state. This prevents success from being explained by a fixed association between an instruction and one command.

Each case has three semantically matched language conditions:

1. English (`en`), retained as a secondary reference;
2. broadly standardised written Spanish (`es_standard`);
3. voseo-marked Rioplatense Spanish (`es_rioplatense`).

The primary inferential comparison is standardised Spanish versus Rioplatense Spanish.

## Decision-structure levels

There are eight cases at each level, comprising two policies with four state variants each.

- **D1 — single-state predicate:** one state field and one conditional threshold/status check.
- **D2 — relational comparison:** comparison between own and opponent state.
- **D3 — Boolean composition:** conjunction or exclusive-or across multiple state facts.
- **D4 — ordered/nested policy:** precedence among multiple conditional branches.
- **D5 — derived numerical state:** arithmetic or distance must be computed from state before selecting an action.
- **D6 — composite policy:** derived or relational state is combined with nested/ordered multi-variable decisions.

The levels are an experimental manipulation of decision structure, not a claim of a universal psychological or computational complexity scale. They differ not only in the number and type of state operations but also, at the upper levels, in branch structure. Raw accuracy across D1–D6 must therefore be interpreted together with the branch diagnostics below rather than as an isolated measure of reasoning complexity.

## Counter-state requirement

Every policy is evaluated in four state variants and must yield at least two distinct correct commands across those states. The instruction wording is held constant within a language condition across the four states. A model therefore has to use the supplied game state to obtain all variants correctly.

This is a counter-state design, not a requirement that terminal commands occur equally often within every policy. Branch frequencies follow the policy logic; for example, a two-condition conjunction is true in one of its four Boolean state combinations. Command-frequency imbalance must therefore not be interpreted as evidence of model preference without comparison to the policy structure.

## Models and invocation

Use these four local model conditions:

- `mistral-small3.2:24b-instruct-2506-q4_K_M`
- `qwen3:30b-a3b-instruct-2507-q4_K_M`
- `qwen3:4b-instruct-2507-q4_K_M`
- `llama3.2:latest`

Use `run_decision_experiment.py` with the strict direct Ollama `/api/chat` transport. The request must transmit and record the exact generation options: temperature `0.0`, seed `20260825` plus repeat index, output-token limit `24`, and `stream: false`. The runner retains BatLLM's production command grammar, strict parser, deterministic execution semantics, and condition randomisation procedure.

The system prompt makes the state-use task explicit: bot 1 is the acting agent (`you`), bot 2 is the opponent, and the model must apply the policy to the supplied state before selecting a command. It instructs the model to evaluate comparisons, Boolean conditions, arithmetic, and ordered/nested branches as written, while keeping reasoning internal and returning only the BatLLM command token. This clarification is identical across all three language conditions and does not supply any Spanish lexical glosses.

Total main-run calls: 48 cases × 3 language conditions × 4 models = **576 calls**.

## Outcomes

The primary outcome is **strict command correctness** under BatLLM's unchanged production parser.

Primary reporting:

- strict accuracy for standardised Spanish and Rioplatense Spanish at D1–D6;
- paired standard-minus-Rioplatense difference at each level;
- discordant-pair counts and exact McNemar result at each level;
- the trajectory of the paired language difference as decision structure changes.

Secondary outcomes:

- strict command validity;
- action-family correctness;
- parameter correctness where applicable;
- deterministic executable-consequence correctness;
- per-model results;
- per-policy counter-state consistency.

Prospectively defined state-use and branch diagnostics:

- **policy-complete correctness:** whether all four counter-states of a policy are answered correctly within a language/model condition;
- **state-invariant output:** whether a model emits the same command for all four states of a policy despite the oracle requiring at least two commands;
- **first-mentioned-action diagnostic:** the rate at which responses select the first terminal action mentioned in a policy, interpreted against that policy's oracle branch frequencies rather than as an accuracy baseline;
- **target branch position:** accuracy stratified by which terminal branch is correct, used to distinguish state/policy failure from language-variety effects when policies have different branch structures.

These diagnostics are explanatory and do not replace strict command correctness as the primary outcome.

A formal language-condition × decision-level interaction analysis may supplement the paired results, but no post-hoc redefinition of the D1–D6 levels is permitted after seeing main-run outputs.

## Pre-freeze pilots and transport audit

Pilot/debug calls collected before the final transport and task specification are excluded from the main dataset.

Early pilots revealed that Qwen3 4B and Qwen3 30B-A3B repeatedly selected the first action named by a conditional policy even when its condition was false, identically across English, standardised Spanish, and Rioplatense Spanish. Inspection confirmed that the expected actions and counter-states were correct. This motivated an explicit decision-task system prompt clarifying the mapping from bot identifiers to `you` and `opponent` and requiring evaluation of the supplied state.

A subsequent audit found a separate transport defect: the pinned Modelito 1.4.5 Ollama provider accepts a `settings` argument but does not include those settings in its `/api/chat` request payload. Consequently, nominal temperature, seed, and output-token settings in the earlier runner were not actually applied. No data collected through that adapter are used in the main analysis. The final runner uses a strict direct Ollama transport that sends the exact request options.

The final direct-transport state-use diagnostic isolated the Qwen failure further. Qwen3 30B-A3B correctly extracted bot 1 health (`5`/`25`) and correctly evaluated whether it was below 15 (`YES`/`NO`), but on the symbolic policy `if health < 15 return A; otherwise B` it returned `A` for both states. The same failure appeared when `A/B` were replaced by BatLLM commands `S1/M`. This shows that the failure occurs at conditional branch execution rather than state extraction, threshold comparison, or BatLLM command parsing.

A final branch-order diagnostic compared two logically equivalent binary policies. Mistral Small 3.2 24B returned the correct action for both states under both formulations. Qwen3 30B-A3B and Qwen3 4B were correct for the true branch and for the complementary/reversed formulation, but returned the first branch's action when the original `health < 15` condition was false. Llama 3.2 produced explanatory prose rather than the requested single symbol in the original formulation and selected the first branch incorrectly for one reversed case. These observations establish that the policy syntax is executable by at least one tested model while motivating the branch-position diagnostics above. They are pilot findings only and are excluded from the main dataset.

## Interpretation constraints

The primary object is the **paired difference between the two matched Spanish conditions**. Because branch structure and oracle action are identical within each standardised-Spanish/Rioplatense pair, a branch-position or first-action bias that affects both conditions equally does not by itself constitute a regional-variety effect.

A decline shared by both Spanish conditions across D1–D6 may reflect increasing state/policy difficulty, changing branch structure, or both. It must not be presented as a pure monotonic reasoning-complexity effect without the branch diagnostics.

A Spanish-variety effect is supported only by a difference between the matched Spanish conditions, especially if that difference changes systematically with decision level or branch position. English is contextual rather than the primary inferential baseline.

Nonsignificant differences do not establish equivalence unless an equivalence margin is defined separately and prospectively.

Claims remain limited to the constructions represented here. The Rioplatense condition primarily manipulates voseo morphology and closely matched phrasing rather than the full lexical, pragmatic, social, or geographic breadth of Rioplatense Spanish.

## Freeze rule

The language/logic review, direct-transport audit, state-use diagnostic, and branch-order diagnostic were completed before the main run. The suite, prompt, expected actions, policy definitions, states, scoring rules, model set, transport, generation settings, and D1–D6 assignments are now frozen for the reported main analysis. Any later change constitutes a separate robustness experiment.
