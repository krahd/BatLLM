# Adversarial review and revision record

## Initial recommendation

**Reject in the submitted form; potentially accept after major revision.**

The central idea was defensible, but the manuscript overstated what the implementation recorded, evaluated replay with a substantially circular design, used a weak overhead comparison, and did not provide false-positive controls. More seriously, the checked-in paper source was truncated and the CI artefact contained no compiled PDF. The implementation and manuscript therefore failed the minimum standard of a reproducible systems paper even though most code tests passed.

## Major findings and corrections

### 1. The paper artefact was broken

**Finding.** `main.tex` ended in corrupted bytes after the related-work section. The CI paper job failed because `IEEEtran.cls` was absent, and no PDF was produced.

**Correction.** The manuscript was rewritten from a clean source, compiled locally, rendered page by page, and visually inspected. CI now installs `texlive-publishers` and `texlive-latex-extra`, rejects LaTeX errors, undefined citations, overfull boxes, and page counts outside four to five pages, and uploads the PDF and log.

### 2. “Reproducibility” was too broad

**Finding.** The original title and exposition could be read as claiming reproducibility of the entire LLM-mediated execution, including model output.

**Correction.** The paper is now titled **From Prompt to State: Verifiable Grounding and Operative Replay for LLM-Mediated Control**. It distinguishes model generation from post-grounding execution and states that it does not regenerate model output.

### 3. “Exact provider request” was technically false

**Finding.** BatLLM records the object passed to its provider adapter, not the provider library's internal request, HTTP headers, wire bytes, hidden defaults, or serving configuration.

**Correction.** Every claim now uses **application-level** or **adapter-boundary invocation record**. The formal model names this object explicitly and treats transport capture as outside scope.

### 4. The evaluation was circular

**Finding.** Recorder and verifier both called the same parser and transition function. Perfect replay could therefore establish little beyond deterministic re-execution of the same code.

**Correction.** A second executable semantics was implemented without importing production gameplay code. Differential testing now compares production and reference command normalisation, state, semantic events, and projectile paths over 5,000 targeted and random cases.

**Residual risk.** Both implementations can embody the same specification error. The paper states this and does not present differential agreement as proof.

### 5. The corpus used scripted responses only

**Finding.** The manuscript risked implying general LLM or provider reproducibility from a deterministic fixture corpus.

**Correction.** Scripted output is now presented as an experimental control for trace semantics. The paper makes no model-quality, live-provider, or network claim. The live Modelito/Ollama adapter remains available as an integration path but is not included in the reference result table.

### 6. Fault injection targeted only the first play

**Finding.** Detection at one trace position did not establish sequence, history, continuity, or final-state checks later in a session.

**Correction.** Play-local perturbations now target early, middle, and late positions; rule mutations remain round-level. Deletion and reordering are exercised away from an unobservable terminal no-op. All derivable commitments are re-anchored before verification.

### 7. There was no false-positive control

**Finding.** A verifier that rejects every non-canonical file could appear strong under mutation testing.

**Correction.** Every reference trace is reserialised in three semantically identical forms: compact ASCII, pretty Unicode, and recursively reversed key order. The paper reports acceptance as a separate result.

### 8. The overhead baseline was arbitrary

**Finding.** Reporting an expansion ratio against a deliberately minimal action log had no principled interpretation and made the system appear defensive.

**Correction.** The comparison was removed. The paper now reports canonical raw and gzip bytes per play by retention profile and repeated in-memory verification timing. The timing scope and environment dependence are explicit.

### 9. “Privacy modes” implied stronger protection than implemented

**Finding.** The modes govern selected text fields, not all metadata or state; hashes do not hide low-entropy prompts; reduced retention prevents independent grounding verification.

**Correction.** The paper calls them **text-retention profiles** and provides an availability table. It states dictionary-guessing, metadata, and grounding limitations directly. Code identifiers remain stable for compatibility.

### 10. The hash chain was presented too close to chain of custody

**Finding.** Unkeyed hashes cannot authenticate the author or detect comprehensive replacement by a party able to rehash the trace and replace every copy.

**Correction.** The threat model now separates consistency commitments from signatures and requires an external signature, timestamp, or transparency-log anchor for adversarial chain of custody.

### 11. Model identity and inference configuration were incomplete

**Finding.** Requested model name and options do not authenticate weights, provider defaults, quantisation, or serving binaries.

**Correction.** These fields are now described as declarations. The paper does not claim model identity or output regeneration.

### 12. Verification “levels” were not cumulative

**Finding.** Redacted and hash-only profiles can satisfy operative replay without satisfying grounding verification, contradicting a cumulative-level interpretation.

**Correction.** R1–R4 were reformulated as V1–V4 verification predicates. A profile table states exactly which evidence supports each predicate.

### 13. The formal claim lacked assumptions

**Finding.** The earlier model did not clearly state the assumptions under which a successful verification result was meaningful.

**Correction.** The paper now gives a bounded soundness statement requiring deterministic parser and transition semantics, semantic-version agreement, retained response text for grounding, and an uncompromised external anchor. Non-implications are stated alongside it.

### 14. Generalisation exceeded evidence

**Finding.** One game and one scripted corpus cannot empirically establish general agent-system applicability.

**Correction.** The conclusion limits transfer to a design pattern for bounded systems with an explicit command language and deterministic transition function. It does not claim validation across domains.

### 15. The paper was overly defensive in form while still insufficiently precise

**Finding.** Repeated disclaimers obscured the positive contribution, yet key technical boundaries remained ambiguous.

**Correction.** The revision states the contribution affirmatively—verifiable grounding plus operative replay—then contains non-claims in one threat-boundary section and one limitations paragraph. The abstract, title, contribution list, formal model, implementation, and evaluation now use the same terminology.

## Residual limitations after revision

1. The graphical application still emits v2 logs; v3 is a separate headless research path.
2. Live-provider metadata completeness and retry-level evidence are not evaluated.
3. Model weights and serving code are not authenticated.
4. The command normaliser remains a small application-specific parser rather than a formally generated grammar.
5. The independent executable semantics is not a mechanised proof.
6. The approach requires deterministic post-grounding semantics or explicit capture of additional randomness and external effects.
7. Unkeyed commitments require an external trust anchor for adversarial provenance.
8. The evaluation establishes software invariants, not human learning, strategic quality, or ecological validity.

## Revised recommendation

**Acceptable as a compact systems paper once the complete CI workflow is green and its generated result macros agree with the manuscript.** The revised contribution is narrow but real: it identifies a verifiable boundary between stochastic linguistic output and deterministic application semantics and implements that boundary as an inspectable artefact.
