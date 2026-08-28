# GlobalSouthAI 2026: institutional action-surface audit and pilot

This directory is the implementation-owned research artefact for *What Becomes a Tool?*.
The editable manuscript remains in the academic-writing repository.

## Research question

How much of an agent's apparent administrative capability is supplied by an institutional environment that has already been made machine-actionable?

The experiment holds a single actor class fixed:

> an external, non-governmental actor without a pre-existing accreditation or contract with the service owner, acting on behalf of a person entitled to the service.

Authentication and authorisation are therefore part of the observed action surface. An API that exists but is only available to a public body, accredited institution, or approved contractual partner is not natively callable for this actor.

## Evidence layers

The artefact deliberately separates two forms of evidence.

1. **Institutional surface audit.** Public documentation is coded per operation. Non-callability is data. The four classes are `native_callable`, `human_facing_only`, `intermediary_required`, and `no_machine_actionable_path`.
2. **Agent pilot.** Safe read-only operations are exposed to an agent through native and normalised tool sets. Restricted operations are never called with real identities or credentials: the normalised arm uses faithful, explicitly counterfactual fixtures with the same abstract operation. The agent runner records both whether the agent made the right decision and whether the task could be completed under the arm's actual affordances.

This avoids treating a restricted API as if it were public, avoids mutating public administrative state, and avoids consuming scarce appointments or other public resources.

## Provenance model

Every callable route records where its actionability is supplied:

- `institution`: an official machine-actionable route exposed under the actor's ordinary access rules;
- `harness`: a benchmark/runtime tool supplied by the experimental environment;
- `intermediary`: a third-party wrapper or broker not supplied by the institution.

Normalised tools are always marked `harness`. They are not evidence that the institution itself is callable.

## Adapter derivation rule

Normalised adapters are derived once from the abstract operation ontology before model execution. They use stable verbs and fields across jurisdictions, preserve documented source semantics, and cannot add records or privileges unavailable to the scoped actor. No model-specific tool descriptions or task-specific prompt tuning are permitted. Restricted/sensitive operations use synthetic fixture values only.

## Pilot design

The default pilot crosses:

- model family: at least two materially different local models;
- arm: `native` and `normalised`;
- instruction language: Portuguese and English;
- repetition: three runs per cell by default.

Primary metrics are overall task completion, availability ceiling, conditional completion when a route exists, correct tool/no-tool decision, schema-valid calls, and latency. Failure classes include `surface_unavailable`, `wrong_tool`, `invalid_arguments`, `execution_error`, and `model_noncompliance`.

The language crossing is a control, not a claim that Portuguese and English interfaces are interchangeable. The equal-documentation synthetic controls estimate how much performance can move when two semantically equivalent surfaces receive matched documentation.

## Reproduction

Static validation requires only Python 3.10+:

```bash
python research/globalsouthai2026/experiments/validate.py
python research/globalsouthai2026/experiments/run_pilot.py --backend deterministic --repetitions 3
python research/globalsouthai2026/experiments/summarise.py results/globalsouthai-runs.jsonl
```

For model executions, an Ollama server is expected at `http://127.0.0.1:11434`:

```bash
python research/globalsouthai2026/experiments/run_pilot.py \
  --backend ollama \
  --models qwen2.5:0.5b llama3.2:1b \
  --languages pt en \
  --arms native normalised \
  --repetitions 3
```

The GitHub Actions workflow `.github/workflows/globalsouthai.yml` performs validation and a small two-model execution and uploads raw traces plus summaries as an artefact. It does not commit generated results automatically.

## Audit scope

The Brazil corpus is the empirical centre of the pilot. India and Kenya are scoped documentary audits used only to test whether the conceptual categories travel; they are not pooled into a country ranking. Cross-jurisdiction differences remain confounded by task equivalence, language, model familiarity, authentication regimes, documentation practices, and institutional purpose.

## Safety and ethics

- no real personal identifiers are committed or used by the fixtures;
- no state-changing government endpoint is called;
- no appointments, applications, payments, registrations, or scarce public resources are consumed;
- no restricted credential is requested or simulated as genuine access;
- live checks, when enabled, are limited to documented public GET endpoints and are cached into run artefacts;
- a failed or forbidden route is recorded as an affordance property rather than bypassed.
