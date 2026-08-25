# LXAI 2026 main-run results

**Dataset:** `results/20260825T094526Z/`  
**State:** frozen direct-transport main run complete; 576/576 calls; zero provider errors.  
**Raw files:** `metadata.json`, `results.csv`, `results.jsonl`, `summary.json`.  
**Derived diagnostics:** `results/20260825T094526Z/DECISION-ANALYSIS.md`, `decision_analysis.json`.

## Strict command correctness

| Model | English | Standard Spanish | Rioplatense | Std − Rio |
|---|---:|---:|---:|---:|
| Mistral Small 3.2 24B | 56.2% | 50.0% | 41.7% | +8.3 pp |
| Qwen3 30B-A3B | 43.8% | 45.8% | 50.0% | −4.2 pp |
| Qwen3 4B | 50.0% | 35.4% | 35.4% | 0.0 pp |
| Llama 3.2 | 12.5% | 10.4% | 20.8% | −10.4 pp |

Across the 192 matched standard-Spanish/Rioplatense case/model pairs:

- standard Spanish: 68/192 = 35.4%;
- Rioplatense: 71/192 = 37.0%;
- standard-only correct: 9;
- Rioplatense-only correct: 12;
- standard minus Rioplatense: −1.56 percentage points;
- exact McNemar p = 0.6636.

No prospectively defined equivalence margin exists. The nonsignificant paired result is therefore not an equivalence result.

Per-model exact McNemar results for strict correctness:

- Mistral 24B: standard-only 6, Rioplatense-only 2, p = 0.2891;
- Qwen3 30B-A3B: standard-only 2, Rioplatense-only 4, p = 0.6875;
- Qwen3 4B: no discordant Spanish pairs; p undefined;
- Llama 3.2: standard-only 1, Rioplatense-only 6, p = 0.1250.

The direction is heterogeneous across the four fixed model conditions. Do not infer a model-population effect from the pooled descriptive result.

## Strict correctness by decision-structure tier

| Tier | Standard Spanish | Rioplatense | Std − Rio | Exact McNemar p |
|---|---:|---:|---:|---:|
| D1 | 40.6% | 40.6% | 0.0 pp | 1.000 |
| D2 | 43.8% | 43.8% | 0.0 pp | n/a (no discordance) |
| D3 | 37.5% | 31.2% | +6.25 pp | 0.688 |
| D4 | 40.6% | 46.9% | −6.25 pp | 0.500 |
| D5 | 28.1% | 37.5% | −9.38 pp | 0.375 |
| D6 | 21.9% | 21.9% | 0.0 pp | 1.000 |

There is no monotonic Rioplatense penalty as D1–D6 changes. D1 and D2 are identical across Spanish conditions; the sign changes at D3/D4; Rioplatense is descriptively higher at D5; D6 is identical. D1–D6 are designed structural strata, not a validated interval-scale complexity measure.

## Other outcome metrics

### Action-family correctness

Across 192 Spanish pairs:

- standard Spanish: 40.1%;
- Rioplatense: 43.2%;
- standard minus Rioplatense: −3.13 pp;
- standard-only 9, Rioplatense-only 15;
- exact McNemar p = 0.3075.

### Executable-consequence correctness

Across 192 Spanish pairs:

- standard Spanish: 43.8%;
- Rioplatense: 42.2%;
- standard minus Rioplatense: +1.56 pp;
- standard-only 11, Rioplatense-only 8;
- exact McNemar p = 0.6476.

The sign of the small pooled Spanish difference therefore depends on the outcome definition: strict command correctness slightly favours Rioplatense, while executable-consequence correctness slightly favours standard Spanish. Neither difference is statistically decisive. This is evidence against a simple stable pooled regional-variety direction in this bounded suite.

Executable correctness by tier:

| Tier | Standard Spanish | Rioplatense | Std − Rio | Exact McNemar p |
|---|---:|---:|---:|---:|
| D1 | 56.2% | 53.1% | +3.12 pp | 1.000 |
| D2 | 50.0% | 50.0% | 0.0 pp | n/a |
| D3 | 40.6% | 34.4% | +6.25 pp | 0.688 |
| D4 | 56.2% | 46.9% | +9.38 pp | 0.250 |
| D5 | 34.4% | 43.8% | −9.38 pp | 0.375 |
| D6 | 25.0% | 25.0% | 0.0 pp | 1.000 |

### Validity and failure classes

- Correct strict commands: 217/576 = 37.7%.
- Valid but wrong action (`action_error`): 352.
- Invalid/unrecoverable: 7.
- Format-only: 0.
- Format + action error: 0.
- Provider errors: 0.

All Mistral/Qwen responses were valid. The seven invalid outputs were confined to Llama 3.2. The dominant failure is therefore action selection rather than provider or formatting failure.

## Policy-level state-use diagnostics

The prospectively declared diagnostics were derived from the frozen CSV by `analyze_decision_results.py`; the derived files are committed beside the raw results.

| Condition | Policy-complete | State-invariant | First-action selected | Oracle first-action | Excess |
|---|---:|---:|---:|---:|---:|
| English | 3/48 (6.2%) | 37/48 (77.1%) | 63.0% | 43.8% | +19.3 pp |
| Standard Spanish | 0/48 (0.0%) | 37/48 (77.1%) | 57.8% | 43.8% | +14.1 pp |
| Rioplatense | 0/48 (0.0%) | 36/48 (75.0%) | 59.9% | 43.8% | +16.1 pp |

A policy group is `model × language condition × policy`, evaluated over its four counter-states. In the two Spanish conditions combined, none of 96 groups answered all four counter-states correctly, and 73/96 (76.0%) emitted one invariant command despite the oracle requiring more than one command across the four states. First-mentioned actions were selected substantially more often than their oracle frequency in both Spanish conditions.

This is the strongest explanatory result of the study: the models frequently fail to condition action selection on the supplied state. The state-use failure is large in both Spanish varieties and is much larger than the small pooled standard-vs-Rioplatense difference.

### Spanish policy diagnostics by model

| Model | Condition | Policy-complete | State-invariant | First-action excess |
|---|---|---:|---:|---:|
| Llama 3.2 | Standard | 0/12 | 10/12 (83.3%) | −29.2 pp |
| Llama 3.2 | Rioplatense | 0/12 | 8/12 (66.7%) | −16.7 pp |
| Mistral 24B | Standard | 0/12 | 7/12 (58.3%) | +14.6 pp |
| Mistral 24B | Rioplatense | 0/12 | 9/12 (75.0%) | +25.0 pp |
| Qwen3 30B-A3B | Standard | 0/12 | 11/12 (91.7%) | +50.0 pp |
| Qwen3 30B-A3B | Rioplatense | 0/12 | 9/12 (75.0%) | +37.5 pp |
| Qwen3 4B | Standard | 0/12 | 9/12 (75.0%) | +20.8 pp |
| Qwen3 4B | Rioplatense | 0/12 | 10/12 (83.3%) | +18.8 pp |

The first-action diagnostic is explanatory rather than a universal bias measure: Llama often selected other recurrent actions, yielding negative excess, while the Qwen models showed especially strong first-action excess. The common cross-model feature is state-invariant output, not one single lexical heuristic.

### Spanish state invariance by tier

| Tier | Standard | Rioplatense |
|---|---:|---:|
| D1 | 6/8 (75.0%) | 5/8 (62.5%) |
| D2 | 7/8 (87.5%) | 8/8 (100.0%) |
| D3 | 5/8 (62.5%) | 4/8 (50.0%) |
| D4 | 7/8 (87.5%) | 6/8 (75.0%) |
| D5 | 5/8 (62.5%) | 6/8 (75.0%) |
| D6 | 7/8 (87.5%) | 7/8 (87.5%) |

State-invariant behaviour is already prevalent at D1 and remains high across the designed strata. This prevents interpreting a raw D1→D6 decline as a clean effect of increasing decision complexity.

## Interpretation supported by the full analysis

The main run does not show the hypothesised pooled disadvantage for voseo-marked Rioplatense instructions, nor a stable pooled regional-variety direction. More importantly, the counter-state analysis shows that model outputs are usually insensitive to state changes that require different actions.

The strongest bounded interpretation is:

> In this controlled executable suite, regional Spanish marking is not the dominant source of failure. Across both standardised and voseo-marked Rioplatense Spanish, models frequently fail to condition their selected action on the supplied state; state-invariant policy execution and model-specific action-selection behaviour dominate the small, unstable regional-variety difference.

Do not convert this into an equivalence claim, a statement that models “understand” Rioplatense, a general robustness claim, or a claim about internal mechanisms. The experiment is behavioural and bounded to these constructions, policies and four fixed local model conditions.
