# BatLLM URUCON 2026 research artefact

This directory contains the implementation, evaluation, and manuscript for **From Prompt to State: Verifiable Grounding and Operative Replay for LLM-Mediated Control**.

## Scope

The artefact implements a schema-v3 research execution path inside BatLLM. It records the application-level object passed to the provider adapter, preserves or commits to returned text, records response-to-command grounding, freezes game rules, and verifies resulting state and semantic events through BatLLM's pure transition engine.

The phrase **application-level invocation** is deliberate. The recorder captures the provider-adapter arguments visible to BatLLM: ordered messages, requested model, endpoint declaration, generation options, and stream setting. It does not claim to capture provider-library internals, HTTP headers, wire bytes, hidden defaults, model weights, or serving binaries.

The graphical application's user-facing export remains schema v2 for compatibility. The paper's claims concern the explicit schema-v3 headless research runtime and verifier.

## Verification predicates

- **V1 — trace validity:** schema, identifiers, sequence, state continuity, final states, commitments, transition commitments, and ordered play chain.
- **V2 — invocation evidence:** independent application-level invocation reconstruction in full retention; retained structure and commitments in redacted retention; commitment only in hash-only retention.
- **V3 — grounding consistency:** re-parsing retained response text must yield the recorded command and status. Hidden response text cannot be independently re-grounded.
- **V4 — operative replay:** the recorded command, pre-state, and frozen rules must derive the recorded post-state and semantic events.

These are verification predicates, not cumulative maturity levels. Availability depends on retained evidence.

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

The live adapter is provided as an integration path; the reference evaluation uses scripted responses to isolate trace and transition semantics from network and model variability.

## Evaluation

```bash
python research/urucon2026/experiments/run_all.py
```

The evaluation performs:

1. generation and verification of 60 traces and 1,080 transitions across all retention profiles;
2. 5,000 differential cases against a separately implemented executable semantics that imports no production gameplay code;
3. re-anchored semantic perturbations at early, middle, and late trace positions, plus round-level rule perturbations;
4. benign JSON serialisation controls using compact ASCII, pretty Unicode, and recursively reversed key order;
5. repeated in-memory verification timing and canonical raw/gzip size measurement; and
6. automatic generation of `paper/results.tex` from result summaries.

Generated corpus files, timing results, and the compiled paper are CI artefacts rather than manually curated evidence. The workflow runs source compilation, schema validation, the complete non-live BatLLM tests, and every research experiment on Linux, macOS, and Windows under Python 3.10–3.12. A separate job compiles and preflights the four-page A4 IEEE manuscript.

## Files

- `schema/batllm-session-v3.schema.json`: machine-readable trace schema.
- `experiments/reference_semantics.py`: independent executable semantics.
- `experiments/differential_semantics.py`: production/reference differential testing.
- `experiments/inject_faults.py`: multi-position re-anchored perturbation testing.
- `experiments/serialization_controls.py`: benign-serialisation false-positive controls.
- `experiments/measure_overhead.py`: raw/gzip size and repeated in-memory timing.
- `paper/main.tex`: manuscript source.
- `CLAIMS.md`: claim-to-evidence ledger.
- `PAPER_REVIEW.md`: adversarial paper review and revision record.
- `AUDIT.md`: final implementation and manuscript audit.

## Security and disclosure boundary

SHA-256 values are unkeyed consistency commitments, not signatures. They do not authenticate an author, prevent comprehensive trace replacement, or conceal low-entropy content from dictionary guessing. External chain of custody requires an independent signature, trusted timestamp, or transparency-log anchor.

The `full`, `redacted`, and `hashed` profiles govern prompt, system-instruction, response, and request-message text. They do not imply that all metadata or game state is private. Reduced retention preserves operative replay but cannot independently verify the response-to-command mapping.
