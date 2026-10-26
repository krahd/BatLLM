# Frozen-run audit

Source: `research/lxai2026/results/20260825T094526Z`

This is post-hoc descriptive audit output. It does not alter the frozen dataset.

## Language-pair comparisons

| Metric | Left | Right | Left acc. | Right acc. | Left-only | Right-only | Δ left−right | exact McNemar p |
|---|---|---|---:|---:|---:|---:|---:|---:|
| command_correct | English | Tuteo Spanish | 40.6% | 35.4% | 17 | 7 | +5.2 pp | 0.0639 |
| command_correct | English | Rioplatense voseo | 40.6% | 37.0% | 20 | 13 | +3.6 pp | 0.2962 |
| command_correct | Tuteo Spanish | Rioplatense voseo | 35.4% | 37.0% | 9 | 12 | -1.6 pp | 0.6636 |
| action_family_correct | English | Tuteo Spanish | 43.8% | 40.1% | 14 | 7 | +3.6 pp | 0.1892 |
| action_family_correct | English | Rioplatense voseo | 43.8% | 43.2% | 17 | 16 | +0.5 pp | 1.0000 |
| action_family_correct | Tuteo Spanish | Rioplatense voseo | 40.1% | 43.2% | 9 | 15 | -3.1 pp | 0.3075 |
| executable_correct | English | Tuteo Spanish | 47.9% | 43.8% | 16 | 8 | +4.2 pp | 0.1516 |
| executable_correct | English | Rioplatense voseo | 47.9% | 42.2% | 21 | 10 | +5.7 pp | 0.0708 |
| executable_correct | Tuteo Spanish | Rioplatense voseo | 43.8% | 42.2% | 11 | 8 | +1.6 pp | 0.6476 |

## Trivial suite baselines

- Oracle command distribution: `{'S0': 5, 'B': 15, 'S1': 12, 'M': 5, 'A90.0': 3, 'C90.0': 4, 'M0.1': 4}`.
- Oracle action-family distribution: `{'shield': 17, 'shoot': 15, 'move': 9, 'rotate': 7}`.
- Always `B`: 15/48 (31.2%).
- Always `shield` action family: 17/48 (35.4%).
- Always first-mentioned action: 21/48 (43.8%).

## Policy-group overlap

| Condition | Complete | State-invariant | Locked to first | Invariant + first | Invariant, not first |
|---|---:|---:|---:|---:|---:|
| English | 3/48 | 37/48 | 25/48 | 25/48 | 12/48 |
| Tuteo Spanish | 0/48 | 37/48 | 24/48 | 24/48 | 13/48 |
| Rioplatense voseo | 0/48 | 36/48 | 23/48 | 23/48 | 13/48 |

## Strict/executable discrepancy

Executable-correct but strict-command-wrong rows: **40**.
By model: `{'mistral-small3.2:24b-instruct-2506-q4_K_M': 3, 'llama3.2:latest': 37}`.
Command-pair decomposition: `{'S->S0': 12, 'S->S1': 28}`.

## Output/runner checks

- Repeat values: `[0]`; repeats per cell = 1.
- Longest raw response: 4 characters; examples: `['M0.1']`.
- Invalid rows: 7; by condition `{'es_standard': 3, 'en': 4}`; by model `{'llama3.2:latest': 7}`; raw `{'C': 3, 'A': 4}`.
- `diagnostic_command_correct` differs from `command_correct` on 0 / 576 rows.

## Pooled strict accuracy without Llama 3.2

| Condition | Correct | N | Strict accuracy | Executable accuracy |
|---|---:|---:|---:|---:|
| English | 72 | 144 | 50.0% | 50.0% |
| Tuteo Spanish | 63 | 144 | 43.8% | 44.4% |
| Rioplatense voseo | 61 | 144 | 42.4% | 43.8% |

## Parameter correctness

| Model | Condition | Applicable | Correct | Accuracy |
|---|---|---:|---:|---:|
| llama3.2:latest | English | 28 | 2 | 7.1% |
| llama3.2:latest | Tuteo Spanish | 28 | 5 | 17.9% |
| llama3.2:latest | Rioplatense voseo | 28 | 11 | 39.3% |
| mistral-small3.2:24b-instruct-2506-q4_K_M | English | 28 | 20 | 71.4% |
| mistral-small3.2:24b-instruct-2506-q4_K_M | Tuteo Spanish | 28 | 14 | 50.0% |
| mistral-small3.2:24b-instruct-2506-q4_K_M | Rioplatense voseo | 28 | 15 | 53.6% |
| qwen3:30b-a3b-instruct-2507-q4_K_M | English | 28 | 20 | 71.4% |
| qwen3:30b-a3b-instruct-2507-q4_K_M | Tuteo Spanish | 28 | 20 | 71.4% |
| qwen3:30b-a3b-instruct-2507-q4_K_M | Rioplatense voseo | 28 | 20 | 71.4% |
| qwen3:4b-instruct-2507-q4_K_M | English | 28 | 22 | 78.6% |
| qwen3:4b-instruct-2507-q4_K_M | Tuteo Spanish | 28 | 19 | 67.9% |
| qwen3:4b-instruct-2507-q4_K_M | Rioplatense voseo | 28 | 19 | 67.9% |
