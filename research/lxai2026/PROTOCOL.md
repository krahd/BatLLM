# LXAI 2026 Rioplatense executable-action experiment protocol

Protocol frozen before the main four-model run.

## Research question

When semantically matched action instructions differ only in language condition, does executable action fidelity differ between broadly standardised written Spanish and voseo-marked Rioplatense Spanish in a bounded LLM-mediated action environment?

English is retained as a secondary reference condition, not as the primary inferential comparison.

## Scope

This first study operationalises Rioplatense Spanish conservatively, primarily through voseo morphology and closely matched naturalistic phrasing. It does not claim to represent the full lexical, pragmatic, sociolinguistic, or geographic diversity of Rioplatense Spanish.

## Experimental unit

The suite contains 30 semantic cases. Every case has three semantically matched variants:

1. English (`en`)
2. broadly standardised written Spanish (`es_standard`)
3. voseo-marked Rioplatense Spanish (`es_rioplatense`)

Cases cover direct actions, parameterised actions, and state-conditioned actions. The linguistic tiers are balanced across minimal morphology, clause-level voseo, and closely matched naturalistic instructions.

## Models

The main run uses these four locally installed Ollama models as fixed model conditions:

- `mistral-small3.2:24b-instruct-2506-q4_K_M`
- `qwen3:30b-a3b-instruct-2507-q4_K_M`
- `qwen3:4b-instruct-2507-q4_K_M`
- `llama3.2:latest`

The runner records exact Ollama model metadata/digests when available, together with the BatLLM Git commit, suite SHA-256, system-prompt SHA-256, Python version, and Ollama version.

## Invocation protocol

Each trial is stateless. The model receives the same English command grammar and the same serialised game-state format in every linguistic condition. The linguistic manipulation is confined to `[PLAYER_INPUT]`.

Default invocation settings:

- temperature: `0.0`
- seed: `20260825`
- output token limit: `24`
- repeats: `1`
- condition and case order: deterministic randomisation from `20260825`

The system prompt explicitly requests exactly one BatLLM command token and prohibits JSON, dictionaries, prose, Markdown, and code fences.

## Primary outcome

The primary outcome is **strict command correctness** under BatLLM's unchanged production parser. A response is correct only when the text itself is a valid BatLLM command and normalises to the expected command.

The primary comparison is paired `es_standard` versus `es_rioplatense` correctness within the same semantic case and model.

Report:

- condition accuracies and paired differences;
- discordant-pair counts;
- exact McNemar results per model;
- task-class and linguistic-tier breakdowns as secondary analyses.

The pooled all-model result is descriptive because the four models are fixed experimental conditions rather than a random sample of models.

## Secondary outcomes

Secondary measures are:

- strict command validity;
- action-family correctness;
- parameter correctness where applicable;
- deterministic executable-consequence correctness;
- failure class.

A diagnostic layer may recover an unambiguous command only from an explicit mapping field named `command`, for example `{'command': 'S1'}`. This diagnostic never changes the strict parser result, executable result, or primary outcome.

Failure classes are:

- `correct`
- `format_only`
- `format_and_action_error`
- `action_error`
- `invalid_unrecoverable`
- `provider_error`

## Pilot runs

Runs completed before this protocol freeze are debugging/pilot data and must not be pooled with the main experimental dataset. They exposed two implementation issues that were corrected before freeze:

- Kivy argument parsing consumed experiment CLI flags;
- random smoke-test limiting did not preserve matched language groups.

A later pilot also exposed wrapped command outputs, motivating the diagnostic failure taxonomy without changing the strict production parser.

## Interpretation constraints

A language-invariant error, such as selecting the same wrong numerical parameter in all three variants of a case, is a model/action-grounding error and is not evidence of a Rioplatense effect.

No result should be described as evidence about Spanish varieties in general. Claims are limited to the matched constructions represented in this suite and these fixed model conditions.

After the main run begins, prompts, expected actions, scoring rules, model set, and suite cases should remain unchanged for the reported main analysis. Any later altered suite or model set must be reported as a separate experiment or robustness analysis.
