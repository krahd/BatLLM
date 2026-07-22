# Adversarial paper audit: argument, prose, and evidentiary alignment

Date: 22 July 2026  
Audited base: `main` at `3945d521ac1188db3338d60caed602aad421e5ae`

## Verdict before revision

The manuscript was technically defensible but rhetorically not ready for submission. Its abstract did read like an automatically generated engineering summary: it compressed the implementation inventory, verification taxonomy, experiment matrix, and every headline counter into one paragraph before establishing why the problem matters. The rest of the paper repeatedly reproduced the same pattern.

The problem was not excessive anecdote. The manuscript contained almost no anecdotal material. Its weakness was the opposite: the concrete interaction had disappeared behind schemas, predicates, profiles, counters, and boundary statements. A reader could understand that substantial engineering had been completed without clearly understanding the intellectual result.

## Principal weaknesses

### 1. The abstract advertised machinery rather than a contribution

The previous abstract led with a conceptual distinction, then immediately enumerated the trace fields, four predicates, schema, retention profiles, commitments, recorder, verifier, reference semantics, and seven numerical results. This resembled a release note or CI summary. It made the reader reconstruct the paper's contribution from an inventory of components.

### 2. The language-to-state problem remained abstract

The paper described the stochastic model boundary and deterministic execution boundary correctly, but gave no compact example showing why a prompt-response log is insufficient. Consequently, the paper's relevance emerged only after the formal model.

### 3. BatLLM was under-described as the research object

The manuscript named the game and listed its actions, but did not initially give the reader a clear picture of the mediated interaction: a human instruction, a model response such as `C90`, command grounding, and a deterministic state transition. The platform therefore appeared interchangeable with any test harness rather than an intentionally bounded domain.

### 4. Repetition produced an automated tone

Several sections used parallel four-part or five-part constructions, followed by a paragraph of non-claims. The same distinctions were restated in the abstract, introduction, formal model, discussion, and conclusion. This made the prose feel generated even where every sentence was accurate.

### 5. Perfect fixture results were presented too much like product validation

The counts are legitimate coverage results: 60 sessions, 1,080 transitions, 5,000 differential cases, 1,560 re-anchored perturbations, and 180 benign serialisations. Without immediate qualification, however, the sequence of perfect counts reads as a CI dashboard rather than scientific evidence. The manuscript needed to state more directly that these are exhaustive results for declared fixtures, not estimates of deployment reliability.

### 6. Caveats obscured the positive claim

The previous version was appropriately cautious, but repeated scope restrictions often displaced the affirmative result. The paper should say once, clearly, what it establishes: retained linguistic evidence can be connected to a grounded command and replayed domain consequence without reproducing model inference.

### 7. One repository claim was stale

The implementation section stated that the artefact was distributed on the `urucon` branch. The paper and research package are now on `main`.

### 8. Reference metadata needed minor correction

The cited works were checked against primary or official sources. The references are real and relevant. Corrections were made to:

- use the current displayed title *From Agent Traces to Trust: A Survey of Evidence Tracing and Execution Provenance in LLM Agents*;
- identify OpenTelemetry's current Generative AI Semantic Conventions and version rather than the older attribute-registry wording;
- identify BatLLM as version 0.3.6 software.

## Claim-to-code verification

The revised paper retains only claims supported by the implementation:

- `research_runtime.py` materialises model, messages, options, stream setting, and declared provider/endpoint immediately before the adapter invocation.
- In full retention, `trace_verifier.py` reconstructs the current user message and conversation history from separately stored prompt, state, system instructions, and context policy.
- Grounding verification re-runs the production parser against retained response text and checks the normalised command and validity status.
- Operative replay re-applies the production transition function under recorded rules and compares state and ordered semantic events.
- `reference_semantics.py` imports no production gameplay module and supports differential testing of parsing and game semantics.

The following boundaries remain material:

- V4 replay itself uses production transition code; independence is supplied by the separate differential experiment, not by every replay.
- The reference implementation is not a mechanised proof and can share specification errors with production code.
- The evaluation corpus uses scripted responses and validates trace semantics rather than live-model behaviour.
- Adapter-boundary records are not transport captures and do not authenticate weights, serving binaries, or hidden provider defaults.
- Unkeyed SHA-256 commitments provide consistency, not authorship, confidentiality, or chain of custody.
- Redacted and hash-only retention cannot independently verify response-to-command grounding.

## Revision performed

The manuscript was rewritten around a single argument: consequential behaviour occurs at the language-to-state boundary, and that boundary can be made auditable.

Changes include:

- replacing the inventory-style abstract with a problem-contribution-result abstract;
- opening with a concrete `C90` transition that exposes the missing evidence;
- explaining BatLLM's role before presenting the formal contract;
- reducing the contribution list to three substantive claims;
- consolidating related work around games, provenance, and replay;
- renaming the central section to *A Contract for the Language-to-State Boundary*;
- making retention-dependent evidence a direct disclosure trade-off;
- describing the evaluation as fixture-based coverage rather than a deployment success rate;
- consolidating caveats into the formal interpretation, discussion, and one limitations paragraph;
- correcting the repository branch and reference metadata;
- balancing the final reference columns.

## Residual weaknesses

The paper remains a narrow four-page systems contribution. It does not evaluate human learning, interaction quality, live-provider behaviour, or cross-domain transfer. BatLLM's schema-v3 path remains separate from the graphical application's schema-v2 export. These are appropriate limitations for this paper, but they prevent the work from supporting broader HCI or AI-literacy claims.

## Revised recommendation

**Submit after the repository checks and generated artefact refresh pass.**

The revised paper now communicates a specific contribution rather than a list of engineering outputs: it defines and implements a verifiable connection between application-visible model interaction, response grounding, and deterministic domain consequence. The result is modest, testable, and relevant to bounded LLM-mediated systems.
