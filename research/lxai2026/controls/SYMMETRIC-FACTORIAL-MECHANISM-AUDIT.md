# Symmetric factorial mechanism audit

Run: `/Users/tom/devel/projects/BatLLM/research/lxai2026/controls/symmetric_clause_factorial/20260825T165129Z`

## Truth × first-position split

| Interface | Oracle first | Oracle second | First selected | Position-only null |
|---|---:|---:|---:|---:|
| direct | 116/128 (90.6%) | 19/128 (14.8%) | 214/256 (83.6%) | 50.0% |
| deliberative | 120/128 (93.8%) | 118/128 (92.2%) | 122/256 (47.7%) | 50.0% |

Wilson 95% intervals:
- direct / oracle_is_first: 90.6% [84.3, 94.6].
- direct / oracle_is_second: 14.8% [9.7, 22.0].
- deliberative / oracle_is_first: 93.8% [88.2, 96.8].
- deliberative / oracle_is_second: 92.2% [86.2, 95.7].

## Deliberative extraction/length diagnostic

- failed extraction: {'n': 15, 'mean': 762.8666666666667, 'median': 758, 'min': 671, 'max': 989, 'p99_nearest_rank': 989}
- successful extraction: {'n': 241, 'mean': 265.10788381742736, 'median': 237, 'min': 66, 'max': 830, 'p99_nearest_rank': 755}

Failures by model/language/order:
- qwen3:30b-a3b-instruct-2507-q4_K_M | es_rioplatense | a_first: 3
- qwen3:30b-a3b-instruct-2507-q4_K_M | es_rioplatense | b_first: 9
- qwen3:30b-a3b-instruct-2507-q4_K_M | es_standard | b_first: 3

Response characters by model/language:
- mistral-small3.2:24b-instruct-2506-q4_K_M | es_rioplatense: {'n': 64, 'mean': 170.59375, 'median': 174.0, 'min': 73, 'max': 334, 'p99_nearest_rank': 334}
- mistral-small3.2:24b-instruct-2506-q4_K_M | es_standard: {'n': 64, 'mean': 166.984375, 'median': 175.5, 'min': 66, 'max': 336, 'p99_nearest_rank': 336}
- qwen3:30b-a3b-instruct-2507-q4_K_M | es_rioplatense: {'n': 64, 'mean': 472.921875, 'median': 436.0, 'min': 206, 'max': 989, 'p99_nearest_rank': 989}
- qwen3:30b-a3b-instruct-2507-q4_K_M | es_standard: {'n': 64, 'mean': 366.59375, 'median': 304.0, 'min': 213, 'max': 830, 'p99_nearest_rank': 830}

Failure suffixes (diagnostic only):
- `ndition for "avanza" (move forward) is satisfied.↵↵Therefore, the correct action`
- `to the policy, you should set the shield on.↵↵Command: S1 (set shield on)↵↵FINAL`
- `ans: If your health is at least 10 more than the opponent's, fire.↵   - But 29 -`
- `ction is required.↵- But in the game, we must choose a command. Since the policy`
- `is means: if your health is at least 10 more than the opponent's, fire.↵   - But`
- `the first condition applies: "When both shields are in the same state, shoot."↵↵`
- `diciones del "O", se debe disparar.↵↵Por lo tanto, la acción es: B (disparar).↵↵`
- ` has shield on, Bot 2 has shield off).↵↵Therefore, the condition "exactly one of`
- `1 has shield on, Bot 2 has shield off).  ↵→ This matches the second condition: "`
- `ntos más") is **false**, so we do **not** activate the shield.↵↵2. "Cuando tenés`
- `o the policy, you should set the shield on.↵↵Command: S1 (set shield on)↵↵FINAL:`
- `dition for "avanzá" is met.↵↵Therefore, the correct action is to move forward.↵↵`
- ` the first condition applies: both shields are in the same state → fire.↵↵FINAL:`
- `val, levantá el escudo."↵   - This means: If your health < opponent's health + 1`
- ` de salud más" is FALSE → do NOT raise the shield.↵↵2. "Cuando tenés al menos 10`

## Language correctness

- direct / es_rioplatense: raw 68/128 (53.1%); given valid 68/128 (53.1%); extraction errors 0.
- direct / es_standard: raw 67/128 (52.3%); given valid 67/128 (52.3%); extraction errors 0.
- deliberative / es_rioplatense: raw 114/128 (89.1%); given valid 114/116 (98.3%); extraction errors 12.
- deliberative / es_standard: raw 124/128 (96.9%); given valid 124/125 (99.2%); extraction errors 3.
