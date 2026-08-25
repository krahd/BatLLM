# LXAI 2026 main-run results

**Dataset:** `results/20260825T094526Z/`  
**State:** frozen direct-transport main run complete; 576/576 calls; zero provider errors.  
**Raw files:** `metadata.json`, `results.csv`, `results.jsonl`, `summary.json`.

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

There is no monotonic Rioplatense penalty as D1–D6 increases. D1 and D2 are identical across Spanish conditions; the sign changes at D3/D4; Rioplatense is descriptively higher at D5; D6 is identical. D1–D6 are designed structural strata, not a validated interval-scale complexity measure.

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

## Interpretation currently supported

The main run does not show the hypothesised pooled disadvantage for voseo-marked Rioplatense instructions. More importantly, it does not show a stable pooled language-variety direction at all: model-specific strict-command differences change sign, the strict and executable pooled metrics point in opposite directions by the same small magnitude, and the D1–D6 Spanish difference is non-monotonic.

The strongest bounded interpretation at this stage is:

> In this controlled executable suite, regional Spanish marking is not the dominant source of failure. Action-selection failures and model-specific behaviour are substantially larger than the small, unstable pooled difference between standardised and voseo-marked Rioplatense Spanish.

Do not convert this into an equivalence claim, a statement that models “understand” Rioplatense, or a general robustness claim.

## Remaining prospectively declared diagnostics

Run:

```bash
python research/lxai2026/analyze_decision_results.py \
  research/lxai2026/results/20260825T094526Z
```

This derives, without altering raw rows:

- policy-complete correctness;
- state-invariant output rate;
- first-mentioned-action selection relative to each policy's oracle branch frequency;
- the same diagnostics by model/condition and tier/condition.

Commit `DECISION-ANALYSIS.md` and `decision_analysis.json` after generation. These diagnostics are explanatory and are required before attributing absolute D1–D6 performance to decision structure.
