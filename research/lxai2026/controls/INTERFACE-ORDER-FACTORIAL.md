# Interface × branch-order factorial analysis

Models: mistral-small3.2:24b-instruct-2506-q4_K_M, qwen3:30b-a3b-instruct-2507-q4_K_M
Conditions: tuteo and Rioplatense voseo
Rows per cell: 128

| Interface | Order | Accuracy | First-position selection | Policy-complete | State-invariant |
|---|---|---:|---:|---:|---:|
| direct | original | 50.0% | 93/128 (72.7%) | 0/32 | 22/32 |
| direct | reordered | 56.2% | 106/128 (82.8%) | 4/32 | 27/32 |
| deliberative | original | 95.3% | 58/128 (45.3%) | 26/32 | 0/32 |
| deliberative | reordered | 96.1% | 66/128 (51.6%) | 29/32 | 0/32 |

Order-swap response changes:

- direct: outputs changed 87/128; changed to newly first-mentioned action 84/87 (96.6%).
- deliberative: outputs changed 11/128; changed to newly first-mentioned action 2/11 (18.2%).

This is a post-freeze descriptive interaction analysis. It does not alter the frozen main dataset.
