# Post-freeze control analysis

Frozen main: `/Users/tom/devel/projects/BatLLM/research/lxai2026/results/20260825T094526Z`

## Explicit-deliberation control

Directory: `/Users/tom/devel/projects/BatLLM/research/lxai2026/controls/deliberation/20260825T153148Z`

| Model | Condition | Main | Deliberation | Δ | Main-only | Control-only | Output changed |
|---|---|---:|---:|---:|---:|---:|---:|
| mistral-small3.2:24b-instruct-2506-q4_K_M | es_rioplatense | 41.7% | 91.7% | +50.0 pp | 1 | 25 | 28/48 |
| mistral-small3.2:24b-instruct-2506-q4_K_M | es_standard | 50.0% | 91.7% | +41.7 pp | 1 | 21 | 25/48 |
| qwen3:30b-a3b-instruct-2507-q4_K_M | es_rioplatense | 50.0% | 97.9% | +47.9 pp | 1 | 24 | 25/48 |
| qwen3:30b-a3b-instruct-2507-q4_K_M | es_standard | 45.8% | 95.8% | +50.0 pp | 1 | 25 | 27/48 |

Policy diagnostics:

- `es_rioplatense`: complete 19/24; state-invariant 0/24.
- `es_standard`: complete 19/24; state-invariant 0/24.

Provider errors: 0; final-line extraction errors: 4; max full response length: 809 characters.

## Branch-order control

Directory: `/Users/tom/devel/projects/BatLLM/research/lxai2026/controls/branch_order/20260825T161504Z`

| Model | Condition | Main | Reordered | Δ | Output changed | New-first after reorder |
|---|---|---:|---:|---:|---:|---:|
| mistral-small3.2:24b-instruct-2506-q4_K_M | en | 65.6% | 50.0% | -15.6 pp | 21/32 | 25/32 |
| mistral-small3.2:24b-instruct-2506-q4_K_M | es_rioplatense | 40.6% | 46.9% | +6.2 pp | 21/32 | 22/32 |
| mistral-small3.2:24b-instruct-2506-q4_K_M | es_standard | 53.1% | 53.1% | +0.0 pp | 20/32 | 26/32 |
| qwen3:30b-a3b-instruct-2507-q4_K_M | en | 46.9% | 59.4% | +12.5 pp | 24/32 | 30/32 |
| qwen3:30b-a3b-instruct-2507-q4_K_M | es_rioplatense | 56.2% | 65.6% | +9.4 pp | 19/32 | 28/32 |
| qwen3:30b-a3b-instruct-2507-q4_K_M | es_standard | 50.0% | 59.4% | +9.4 pp | 27/32 | 30/32 |

Position-tracking details:

- `mistral-small3.2:24b-instruct-2506-q4_K_M` / `en`: original-first main 26/32; new-first after reorder 25/32; changed-to-new-first 19/32.
- `mistral-small3.2:24b-instruct-2506-q4_K_M` / `es_rioplatense`: original-first main 23/32; new-first after reorder 22/32; changed-to-new-first 19/32.
- `mistral-small3.2:24b-instruct-2506-q4_K_M` / `es_standard`: original-first main 18/32; new-first after reorder 26/32; changed-to-new-first 19/32.
- `qwen3:30b-a3b-instruct-2507-q4_K_M` / `en`: original-first main 26/32; new-first after reorder 30/32; changed-to-new-first 24/32.
- `qwen3:30b-a3b-instruct-2507-q4_K_M` / `es_rioplatense`: original-first main 23/32; new-first after reorder 28/32; changed-to-new-first 19/32.
- `qwen3:30b-a3b-instruct-2507-q4_K_M` / `es_standard`: original-first main 29/32; new-first after reorder 30/32; changed-to-new-first 27/32.

Provider errors: 0.

