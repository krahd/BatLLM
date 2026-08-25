# LXAI experiment transport audit — 2026-08-25

## Finding

The initial LXAI runners used `ModelitoChatClient`, which calls `Client.summarize(..., settings=options)` through Modelito's Ollama provider.

The pinned dependency used by BatLLM is `modelito==1.4.5`. Inspection of Modelito v1.4.5 showed that `OllamaProvider.summarize()` explicitly ignores its `settings` argument and constructs the `/api/chat` payload with `model` and `messages` but without the requested generation options. Consequently, the initial runs did **not** establish that the nominal `temperature=0.0`, `seed=20260825`, and `num_predict=24` settings were applied by Ollama.

The message list itself is passed as structured messages, so this audit does not establish that the linguistic inputs or system message were lost. The defect concerns generation-option control and the possibility of silent transport fallback.

## Consequence for Experiment 1

The stored run:

- `research/lxai2026/results/20260825T083010Z/`

remains preserved as provenance but is **superseded for the paper's main analysis**. Its observations may be described as an initial run, but it must not be represented as the final controlled dataset with the nominal generation settings.

Experiment 1 should be rerun through `run_experiment_direct.py`, which uses the strict direct Ollama `/api/chat` transport and sends the exact `options` mapping.

## Consequence for Experiment 2

All Experiment 2 runs completed before the direct-transport change are pre-freeze pilots and are excluded from analysis. Experiment 2 now uses `run_decision_experiment.py` with the same strict direct Ollama client.

## Direct transport contract

`direct_ollama_client.py` sends:

- exact system and user messages as structured Ollama chat messages;
- `stream: false`;
- the requested model name;
- the exact generation `options` mapping, including temperature, seed, and `num_predict`.

It has no CLI fallback and no deterministic text fallback. Transport or response-shape failures surface as provider errors in the experiment output.

## Reproducibility rule

For any dataset reported in the LXAI paper, use only runs collected after this transport correction. Preserve exact model digests, Git commit, suite hash, system-prompt hash, Ollama version, and requested generation settings in the run metadata. Do not mix pre-audit and post-audit observations in inferential analyses.
