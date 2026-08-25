# LXAI 2026 Rioplatense executable-action experiment: main-run headline

Main run completed on 2026-08-25 with 360 calls: 30 semantic cases × 3 language conditions × 4 fixed model conditions.

## Strict command correctness

| Model | English | Standardised Spanish | Rioplatense | Rioplatense minus standardised Spanish |
|---|---:|---:|---:|---:|
| `mistral-small3.2:24b-instruct-2506-q4_K_M` | 60.0% | 66.7% | 76.7% | +10.0 pp |
| `qwen3:30b-a3b-instruct-2507-q4_K_M` | 83.3% | 80.0% | 86.7% | +6.7 pp |
| `qwen3:4b-instruct-2507-q4_K_M` | 63.3% | 66.7% | 66.7% | 0.0 pp |
| `llama3.2:latest` | 36.7% | 23.3% | 26.7% | +3.3 pp |

Across the 120 matched standardised-Spanish/Rioplatense model-case pairs:

- standardised Spanish strict accuracy: 59.17%
- Rioplatense strict accuracy: 64.17%
- difference, Rioplatense minus standardised Spanish: +5.0 percentage points
- standardised-only correct pairs: 4
- Rioplatense-only correct pairs: 10
- exact McNemar p-value: 0.1795654296875

The pooled comparison is descriptive because the four models are fixed experimental conditions and model-case observations are not treated as a random sample of models.

## Failure classes

- correct: 221
- action error: 129
- invalid, unrecoverable: 10
- format-only: 0
- format + action error: 0
- provider error: 0

The revised system prompt eliminated the wrapped-command formatting failures seen in the pilot. Remaining failures are therefore predominantly substantive action-selection or parameter-grounding failures rather than output-format artefacts.

## Current interpretation

The main run does **not** provide evidence of a Rioplatense penalty. All four fixed model conditions perform at least as well on the voseo-marked Rioplatense variants as on their semantically matched broadly standardised Spanish counterparts. The pooled direction favours Rioplatense by 5 percentage points, but the exact paired test is not statistically significant.

This must not be described as evidence of equivalence. No equivalence margin was pre-specified, and a non-significant difference does not establish equivalence. The defensible claim is narrower: **within this controlled suite and these four fixed model conditions, we did not observe the hypothesised degradation for voseo-marked Rioplatense instructions.**

A second salient pattern is model capability: strict command correctness varies much more across models than across the two Spanish conditions, from roughly 23–37% for `llama3.2:latest` to roughly 80–87% for `qwen3:30b-a3b-instruct-2507-q4_K_M`.

## Analysis still required before paper freeze

Before writing the final results section, inspect and report:

- per-model discordant pairs and exact McNemar tests;
- task-class breakdowns (`direct`, `parameterised`, `state_conditioned`);
- linguistic-tier breakdowns (`minimal_morphology`, `clause_level_voseo`, `naturalistic`);
- strict validity, action-family, parameter and executable-consequence metrics;
- case-level errors to identify whether any apparent Rioplatense advantage is concentrated in a small subset of constructions;
- confidence intervals/effect-size uncertainty, without retroactively introducing an equivalence claim.

The completed run reported its local result directory as:

`research/lxai2026/results/20260825T083010Z/`

Pilot/debug runs must remain excluded from the main analysis.