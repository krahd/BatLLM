# LXAI 2026 decision complexity × Spanish variety

This protocol defines the main decision-complexity experiment. An earlier baseline run was discarded after a transport audit showed that the Modelito 1.4.5 Ollama adapter did not transmit the nominal generation settings. Its stored results and result-specific interpretation were removed and are not part of the evidence base for this study.

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
- the trajectory of the paired language difference as decision level increases.

Secondary outcomes:

- strict command validity;
- action-family correctness;
- parameter correctness where applicable;
- deterministic executable-consequence correctness;
- per-model results;
- per-policy counter-state consistency.

A formal language-condition × decision-level interaction analysis may supplement the paired results, but no post-hoc redefinition of the D1–D6 levels is permitted after seeing main-run outputs.

## Pre-freeze pilots and transport audit

Pilot/debug calls collected before the final transport and task specification are excluded from the main dataset.

Early pilots revealed that Qwen3 4B and Qwen3 30B-A3B repeatedly selected the first action named by a conditional policy even when its condition was false, identically across English, standardised Spanish, and Rioplatense Spanish. Inspection confirmed that the expected actions and counter-states were correct. This motivated an explicit decision-task system prompt clarifying the mapping from bot identifiers to `you` and `opponent` and requiring evaluation of the supplied state.

A subsequent audit found a separate transport defect: the pinned Modelito 1.4.5 Ollama provider accepts a `settings` argument but does not include those settings in its `/api/chat` request payload. Consequently, nominal temperature, seed, and output-token settings in the earlier runner were not actually applied. No data collected through that adapter are used in the main analysis. The final runner uses a strict direct Ollama transport that sends and records the exact request options.

## Interpretation constraints

A decline shared by both Spanish conditions as D1–D6 increases is evidence about decision difficulty in this bounded task, not dialect disadvantage.

A Spanish-variety effect is supported only by a difference between the matched Spanish conditions, especially if that difference changes systematically with decision level. English is contextual rather than the primary inferential baseline.

Nonsignificant differences do not establish equivalence unless an equivalence margin is defined separately and prospectively.

Claims remain limited to the constructions represented here. The Rioplatense condition primarily manipulates voseo morphology and closely matched phrasing rather than the full lexical, pragmatic, social, or geographic breadth of Rioplatense Spanish.

## Freeze rule

Before the main run, perform a final language/logic review, dry run, and state-use sanity check with the final prompt and direct transport. After the main run begins, do not alter prompts, expected actions, policy definitions, states, scoring rules, model set, transport, generation settings, or decision-level assignments for the reported main analysis. Any later changes constitute a separate robustness experiment.
