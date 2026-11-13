# Format-only control

Format-only run: `/Users/tom/devel/projects/BatLLM/research/lxai2026/controls/format_only/20260825T194809Z`
Reference factorial: `/Users/tom/devel/projects/BatLLM/research/lxai2026/controls/symmetric_clause_factorial/20260825T165129Z`

The format-only arm requires exactly `FINAL: <command>` but explicitly forbids intermediate reasoning. It therefore tests whether the deliberative rescue is attributable merely to the final-output convention rather than permission for intermediate computation.

## Pooled comparison

| Arm | Correct | Valid | First-position | Oracle-first correct | Oracle-second correct | Output changed across order swap | Correct both orders | Follows first in both orders | Policy-complete | State-invariant |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| direct | 135/256 (52.7%) | 256/256 (100.0%) | 214/256 (83.6%) | 116/128 (90.6%) | 19/128 (14.8%) | 98/128 (76.6%) | 19/128 (14.8%) | 91/128 (71.1%) | 3/64 (4.7%) | 51/64 (79.7%) |
| format_only | 130/256 (50.8%) | 256/256 (100.0%) | 171/256 (66.8%) | 99/128 (77.3%) | 31/128 (24.2%) | 83/128 (64.8%) | 27/128 (21.1%) | 58/128 (45.3%) | 3/64 (4.7%) | 40/64 (62.5%) |
| deliberative_256 | 238/256 (93.0%) | 241/256 (94.1%) | 122/256 (47.7%) | 120/128 (93.8%) | 118/128 (92.2%) | 16/128 (12.5%) | 111/128 (86.7%) | 2/128 (1.6%) | 54/64 (84.4%) | 1/64 (1.6%) |

## By model and language

### direct
- mistral-small3.2:24b-instruct-2506-q4_K_M / es_rioplatense: 33/64 correct; 64/64 valid; 48/64 first-position; extraction errors 0.
- mistral-small3.2:24b-instruct-2506-q4_K_M / es_standard: 33/64 correct; 64/64 valid; 47/64 first-position; extraction errors 0.
- qwen3:30b-a3b-instruct-2507-q4_K_M / es_rioplatense: 35/64 correct; 64/64 valid; 58/64 first-position; extraction errors 0.
- qwen3:30b-a3b-instruct-2507-q4_K_M / es_standard: 34/64 correct; 64/64 valid; 61/64 first-position; extraction errors 0.

### format_only
- mistral-small3.2:24b-instruct-2506-q4_K_M / es_rioplatense: 41/64 correct; 64/64 valid; 44/64 first-position; extraction errors 0.
- mistral-small3.2:24b-instruct-2506-q4_K_M / es_standard: 40/64 correct; 64/64 valid; 44/64 first-position; extraction errors 0.
- qwen3:30b-a3b-instruct-2507-q4_K_M / es_rioplatense: 26/64 correct; 64/64 valid; 41/64 first-position; extraction errors 0.
- qwen3:30b-a3b-instruct-2507-q4_K_M / es_standard: 23/64 correct; 64/64 valid; 42/64 first-position; extraction errors 0.

### deliberative_256
- mistral-small3.2:24b-instruct-2506-q4_K_M / es_rioplatense: 63/64 correct; 64/64 valid; 33/64 first-position; extraction errors 0.
- mistral-small3.2:24b-instruct-2506-q4_K_M / es_standard: 63/64 correct; 64/64 valid; 33/64 first-position; extraction errors 0.
- qwen3:30b-a3b-instruct-2507-q4_K_M / es_rioplatense: 51/64 correct; 52/64 valid; 25/64 first-position; extraction errors 12.
- qwen3:30b-a3b-instruct-2507-q4_K_M / es_standard: 61/64 correct; 61/64 valid; 31/64 first-position; extraction errors 3.

