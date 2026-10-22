# LXAI decision diagnostics

Source: `research/lxai2026/results/20260825T094526Z`

## Policy-level diagnostics by condition

| Condition | Policy-complete | State-invariant | First-action selected | Oracle first-action | Excess |
|---|---:|---:|---:|---:|---:|
| English | 3/48 (6.2%) | 37/48 (77.1%) | 63.0% | 43.8% | +19.3 pp |
| Standard Spanish | 0/48 (0.0%) | 37/48 (77.1%) | 57.8% | 43.8% | +14.1 pp |
| Rioplatense | 0/48 (0.0%) | 36/48 (75.0%) | 59.9% | 43.8% | +16.1 pp |

## Spanish conditions by model

| Model | Condition | Policy-complete | State-invariant | First-action excess |
|---|---|---:|---:|---:|
| llama3.2:latest | Standard Spanish | 0/12 (0.0%) | 10/12 (83.3%) | -29.2 pp |
| llama3.2:latest | Rioplatense | 0/12 (0.0%) | 8/12 (66.7%) | -16.7 pp |
| mistral-small3.2:24b-instruct-2506-q4_K_M | Standard Spanish | 0/12 (0.0%) | 7/12 (58.3%) | +14.6 pp |
| mistral-small3.2:24b-instruct-2506-q4_K_M | Rioplatense | 0/12 (0.0%) | 9/12 (75.0%) | +25.0 pp |
| qwen3:30b-a3b-instruct-2507-q4_K_M | Standard Spanish | 0/12 (0.0%) | 11/12 (91.7%) | +50.0 pp |
| qwen3:30b-a3b-instruct-2507-q4_K_M | Rioplatense | 0/12 (0.0%) | 9/12 (75.0%) | +37.5 pp |
| qwen3:4b-instruct-2507-q4_K_M | Standard Spanish | 0/12 (0.0%) | 9/12 (75.0%) | +20.8 pp |
| qwen3:4b-instruct-2507-q4_K_M | Rioplatense | 0/12 (0.0%) | 10/12 (83.3%) | +18.8 pp |

## Spanish conditions by decision tier

| Tier | Condition | Policy-complete | State-invariant | First-action excess |
|---|---|---:|---:|---:|
| D1 | Standard Spanish | 0/8 (0.0%) | 6/8 (75.0%) | +9.4 pp |
| D1 | Rioplatense | 0/8 (0.0%) | 5/8 (62.5%) | +9.4 pp |
| D2 | Standard Spanish | 0/8 (0.0%) | 7/8 (87.5%) | +18.8 pp |
| D2 | Rioplatense | 0/8 (0.0%) | 8/8 (100.0%) | +25.0 pp |
| D3 | Standard Spanish | 0/8 (0.0%) | 5/8 (62.5%) | +21.9 pp |
| D3 | Rioplatense | 0/8 (0.0%) | 4/8 (50.0%) | +12.5 pp |
| D4 | Standard Spanish | 0/8 (0.0%) | 7/8 (87.5%) | +18.8 pp |
| D4 | Rioplatense | 0/8 (0.0%) | 6/8 (75.0%) | +28.1 pp |
| D5 | Standard Spanish | 0/8 (0.0%) | 5/8 (62.5%) | -15.6 pp |
| D5 | Rioplatense | 0/8 (0.0%) | 6/8 (75.0%) | -9.4 pp |
| D6 | Standard Spanish | 0/8 (0.0%) | 7/8 (87.5%) | +31.2 pp |
| D6 | Rioplatense | 0/8 (0.0%) | 7/8 (87.5%) | +31.2 pp |
