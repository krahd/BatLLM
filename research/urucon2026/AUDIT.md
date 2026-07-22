# Final adversarial audit

## Verdict

The paper is defensible as a narrow systems contribution: an evidence contract that connects an application-level LLM invocation and retained response to explicit grounding and deterministic state/event replay. It is not defensible as generic agent provenance, model-output reproducibility, transport capture, or authenticated chain of custody.

## Novelty boundary

The following claims remain prohibited:

- first provenance model for LLM agents;
- first record-and-replay system for agents;
- first trace contract for language-to-action systems;
- first forensic replay of prompt–response interactions;
- first use of games to evaluate or teach LLM interaction.

PROV-AGENT, AgentRR, Prompt Scene Investigation, `agrepl`, Message–Action Trace contracts, W3C PROV, OpenTelemetry, and the 2026 survey of evidence tracing and execution provenance establish substantial prior art. The contribution survives because its verification object is the conjunction:

```text
human instruction and context
→ application-level adapter invocation
→ retained response or commitment
→ explicit response-to-command grounding
→ frozen domain transition
→ recorded state and semantic events
```

## Implementation findings

- Recorder and verifier use the production BatLLM parser and transition engine.
- Full-retention invocation verification reconstructs the current message and conversation history from separately recorded fields rather than trusting a self-hash alone.
- Invocation errors are represented separately and are not counted as model groundings.
- Raw model text is excluded from semantic events after an earlier privacy leak was found and fixed.
- Retention-dependent guarantees are explicit.
- The independent reference semantics imports no production gameplay module.
- Fault injection re-anchors retained-content commitments and targets multiple trace positions.
- Benign serialisation controls test false rejection.
- The paper source compiles to four A4 IEEE pages without overfull boxes, undefined citations, or embedded hyperlinks.

## Residual limitations

- v3 remains a headless research path; the GUI exports v2.
- The adapter record is not a wire capture.
- Requested model identity is declarative, not cryptographically bound to weights or serving binaries.
- Retry count is recorded, but successful-after-retry traces do not preserve every intermediate provider error.
- Scripted responses validate trace semantics rather than live-model behaviour.
- Reference and production semantics can share a specification error.
- Hash commitments are neither signatures nor confidentiality mechanisms.
- Reduced retention cannot independently verify response grounding.
- Transfer beyond BatLLM is architectural, not empirically demonstrated.

## Release criterion

The branch is complete only when:

1. all nine OS/Python research matrix jobs pass;
2. repository dependency and multiplatform workflows pass;
3. the full experiment suite regenerates all summaries and `results.tex`;
4. the paper job compiles a four- or five-page PDF and uploads it;
5. generated metrics agree with the paper; and
6. the final PR diff contains no corrupted or unrelated file.
