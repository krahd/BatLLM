# BatLLM URUCON 2026 research artefact

This directory contains the implementation, evaluation, and manuscript for the paper **From Prompt to State: A Domain-Semantic Reproducibility Contract for Human–LLM-Mediated Control**.

## Scope

The artefact implements a schema-v3 research execution path inside BatLLM. It records the complete provider request when disclosure permits, preserves or commits to the returned text, records the response-to-command grounding, freezes the game rules, and verifies the resulting state and semantic events by replaying the grounded command through BatLLM's pure transition engine.

The existing graphical application's user-facing session export remains schema v2 for compatibility. The paper's claims concern the explicit schema-v3 research runtime and verifier. They do not reinterpret legacy v2 logs as if those logs contained exact provider invocations.

## Reproducibility levels

- **R1 — trace validity and integrity:** schema, identifiers, sequence, state continuity, final states, content commitments, transition commitments, and ordered play chain.
- **R2 — invocation reconstructability:** exact request reconstruction in full mode; retained structure in redacted mode; commitment only in hash-only mode.
- **R3 — grounding consistency:** re-parsing retained response text must yield the recorded command and status. Hidden text cannot be independently re-grounded.
- **R4 — operative replay:** the recorded command, pre-state, and frozen rules must derive the recorded post-state and semantic events.

## Run

From the repository root:

```bash
python run_batllm_research.py --provider scripted --output /tmp/session.json
python run_batllm_verify.py /tmp/session.json
python run_batllm_verify.py /tmp/session.json --json /tmp/report.json
```

A live local-model trace can be created through Modelito and Ollama:

```bash
python run_batllm_research.py --provider ollama --model smollm2 --output /tmp/live-session.json
```

## Evaluation

```bash
python research/urucon2026/experiments/run_all.py
```

The evaluation generates:

- 60 sessions and 1,080 transitions across full, redacted, and hash-only modes;
- replay-fidelity results;
- controlled semantic perturbations with re-anchored retained-content commitments;
- serialized-size and verifier-throughput measurements;
- `paper/results.tex`, consumed directly by the manuscript.

Generated corpus files and environment-specific timing results are CI artefacts rather than source inputs. The `urucon.yml` workflow runs the complete non-live BatLLM test suite and the research evaluation on Linux, macOS, and Windows under Python 3.10–3.12. A separate artefact job preserves the reference corpus, result tables, and compiled paper.

## Files

- `schema/batllm-session-v3.schema.json`: machine-readable trace schema.
- `experiments/`: corpus generation, fault injection, overhead measurement, and result rendering.
- `paper/main.tex`: paper source.
- `CLAIMS.md`: claim-to-evidence ledger.
- `AUDIT.md`: adversarial novelty, implementation, and manuscript audit.

## Security boundary

The SHA-256 values are unkeyed consistency commitments, not signatures. They detect stale or selectively modified records but do not authenticate the author and do not resist a party able to replace and rehash the complete trace. Adversarial chain of custody requires external signing, trusted timestamps, or transparency-log anchoring.
