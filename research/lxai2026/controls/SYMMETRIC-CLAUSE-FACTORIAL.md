# Symmetric clause-order interface factorial

Run: `/Users/tom/devel/projects/BatLLM/research/lxai2026/controls/symmetric_clause_factorial/20260825T165129Z`
Rows: 512; provider errors: 0; final extraction errors: 15

## Pooled interface result

| Interface | Correct | First-position selection | Valid | Median latency | Mean response chars |
|---|---:|---:|---:|---:|---:|
| deliberative | 238/256 (93.0%) | 122/256 (47.7%) | 241/256 (94.1%) | 3773 ms | 294.3 |
| direct | 135/256 (52.7%) | 214/256 (83.6%) | 256/256 (100.0%) | 487 ms | 1.8 |

## Order-pair sensitivity

Each pair is the same model/language/interface/state with the exact same two policy clauses in opposite order.

| Interface | Language | Model | Pairs | Output changed | Correct both orders | Follows first in both orders |
|---|---|---|---:|---:|---:|---:|
| direct | es_standard | mistral-small3.2:24b-instruct-2506-q4_K_M | 32 | 19/32 (59.4%) | 7/32 (21.9%) | 19/32 (59.4%) |
| direct | es_standard | qwen3:30b-a3b-instruct-2507-q4_K_M | 32 | 30/32 (93.8%) | 2/32 (6.2%) | 29/32 (90.6%) |
| direct | es_rioplatense | mistral-small3.2:24b-instruct-2506-q4_K_M | 32 | 22/32 (68.8%) | 6/32 (18.8%) | 17/32 (53.1%) |
| direct | es_rioplatense | qwen3:30b-a3b-instruct-2507-q4_K_M | 32 | 27/32 (84.4%) | 4/32 (12.5%) | 26/32 (81.2%) |
| deliberative | es_standard | mistral-small3.2:24b-instruct-2506-q4_K_M | 32 | 1/32 (3.1%) | 31/32 (96.9%) | 1/32 (3.1%) |
| deliberative | es_standard | qwen3:30b-a3b-instruct-2507-q4_K_M | 32 | 3/32 (9.4%) | 29/32 (90.6%) | 0/32 (0.0%) |
| deliberative | es_rioplatense | mistral-small3.2:24b-instruct-2506-q4_K_M | 32 | 1/32 (3.1%) | 31/32 (96.9%) | 1/32 (3.1%) |
| deliberative | es_rioplatense | qwen3:30b-a3b-instruct-2507-q4_K_M | 32 | 11/32 (34.4%) | 20/32 (62.5%) | 0/32 (0.0%) |

## Policy diagnostics

| Interface | Order | Language | Model | Complete | State-invariant |
|---|---|---|---|---:|---:|
| direct | a_first | es_standard | mistral-small3.2:24b-instruct-2506-q4_K_M | 1/8 | 7/8 |
| direct | a_first | es_standard | qwen3:30b-a3b-instruct-2507-q4_K_M | 0/8 | 7/8 |
| direct | a_first | es_rioplatense | mistral-small3.2:24b-instruct-2506-q4_K_M | 0/8 | 5/8 |
| direct | a_first | es_rioplatense | qwen3:30b-a3b-instruct-2507-q4_K_M | 0/8 | 5/8 |
| direct | b_first | es_standard | mistral-small3.2:24b-instruct-2506-q4_K_M | 1/8 | 7/8 |
| direct | b_first | es_standard | qwen3:30b-a3b-instruct-2507-q4_K_M | 1/8 | 7/8 |
| direct | b_first | es_rioplatense | mistral-small3.2:24b-instruct-2506-q4_K_M | 0/8 | 6/8 |
| direct | b_first | es_rioplatense | qwen3:30b-a3b-instruct-2507-q4_K_M | 0/8 | 7/8 |
| deliberative | b_first | es_standard | mistral-small3.2:24b-instruct-2506-q4_K_M | 8/8 | 0/8 |
| deliberative | b_first | es_standard | qwen3:30b-a3b-instruct-2507-q4_K_M | 7/8 | 0/8 |
| deliberative | b_first | es_rioplatense | mistral-small3.2:24b-instruct-2506-q4_K_M | 7/8 | 0/8 |
| deliberative | b_first | es_rioplatense | qwen3:30b-a3b-instruct-2507-q4_K_M | 3/8 | 1/8 |
| deliberative | a_first | es_rioplatense | mistral-small3.2:24b-instruct-2506-q4_K_M | 8/8 | 0/8 |
| deliberative | a_first | es_rioplatense | qwen3:30b-a3b-instruct-2507-q4_K_M | 6/8 | 0/8 |
| deliberative | a_first | es_standard | mistral-small3.2:24b-instruct-2506-q4_K_M | 7/8 | 0/8 |
| deliberative | a_first | es_standard | qwen3:30b-a3b-instruct-2507-q4_K_M | 8/8 | 0/8 |
