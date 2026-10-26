# BatLLM status

Last updated: 2026-10-26 01:19

## Project and release phase

BatLLM is a Python/Kivy research, education and two-player battle game. Human prompts mediate model commands inside a deterministic game world. Version `0.3.6` remains in `0.x` hardening; stable 1.0 gates are unsigned.

## Current capabilities

- Two players, two bots, round prompts, shared or independent conversation histories, and optional game-state prompt augmentation.
- Asynchronous gameplay requests and guarded callbacks; fresh histories for new games and conversation/state rollback for cancelled rounds.
- Strict native Ollama inference through the shared Modelito 1.4.6 adapter; structured roles, generation options, `stream: false`, explicit deadlines and propagated errors.
- Ollama status, start, warm-up, local inventory, downloads and deletion at BatLLM’s configured endpoint. Shutdown requires an ownership receipt matching endpoint, PID and process creation time; external services remain running.
- Model selection persists after readiness succeeds. Destructive and expensive actions retain confirmation flows.
- Atomic configuration and session persistence. Session-v2 exports contain completed turns, frozen rules and a configuration metadata snapshot, without live metadata queries during saving.
- Game Analyzer validates action records and replay states, and flags response–command disagreement and turn-continuity breaks.
- Headless schema-v3 research runtime and verifier preserve application-level invocation evidence, grounding, replay and semantic-event checks. This does not authenticate model execution or historical traces.

## Environment and commands

Python `3.10`–`3.12` (`3.12` recommended); macOS, Linux and Windows. Homebrew targets Apple Silicon macOS. Runtime dependencies are maintained in `requirements.txt`; the Homebrew subset is in `packaging/homebrew/requirements.txt`.

```bash
python -m pip install -r requirements.txt
python run_batllm.py
python run_game_analyzer.py
python run_tests.py core
python run_tests.py non-live
python tools/check_docs.py
```

Headless validation uses `KIVY_WINDOW=mock`, `KIVY_NO_ARGS=1` and `KIVY_NO_CONSOLELOG=1`. The non-live suite binds temporary loopback HTTP servers and isolates `BATLLM_HOME`. `python run_tests.py full` mutates a real Ollama service and requires explicit maintainer intent.

## Architecture and important paths

- `src/game/`: Kivy coordination, pure replay semantics, histories, v2 sessions and v3 research traces.
- `src/llm/chat.py`: shared strict inference adapter for desktop and research.
- `src/llm/service.py`: BatLLM configuration, bounded management operations and owned-process lifecycle.
- `src/configs/app_config.py`: section-validated defaults/overlay loading and atomic preference writes.
- `src/util/paths.py`: resources, user state and legacy-session copying.
- `src/view/` and `src/analyzer_model.py`: Kivy screens and analyser presentation.
- `create_release_bundles.py`: full source archives and smaller platform runtime bundles; research packaging is separate.
- `research/urucon2026/`: implementation-owned corpus, results, schema, claims and reproducibility package. The editable paper remains in `krahd/academic-writing`.
- `.github/workflows/`: platform, dependency, research and release checks, with actions pinned by commit.
- `README.md`, `docs/USER_GUIDE.md`, `docs/CONTRIBUTING.md` and `docs/RELEASE_CRITERIA_1_0.md`: public, user, developer and release references.

## Configuration and mutable state

Shipped defaults in `src/configs/config.yaml` are read-only. Preferences and relative session directories use `BATLLM_HOME` when set, otherwise the platform user data directory. Legacy checkout JSON sessions are copied on default-directory access without moving originals or overwriting existing files. Absolute session paths retain their meaning. See [state and installation](docs/STATE_AND_INSTALLATION.md).

The main application service facade uses BatLLM preferences. The standalone configuration editor still bypasses that facade and has endpoint, timeout and shutdown-safety defects. Ownership receipts are stored in the user directory, allowing a helper subprocess to start a service that the application can later stop safely.

## Validation evidence

Fresh local Python 3.12/macOS validation of merged main `d86ae05` (PR #62):

- isolated complete non-live suite: `247 passed, 2 skipped`;
- HTTP-level checks cover desktop and research roles/options, non-streaming requests, request deadlines, unavailable servers, missing models, invalid JSON/streamed bodies and malformed or empty responses;
- full Pylint gate: passed, rated `8.89/10` with existing warnings;
- compilation, documentation validation and `git diff --check`: passed;
- release-bundle generation and Homebrew formula generation with dependency resolution/hashes: passed;
- isolated research pipeline and research-package build: passed (60 valid traces, 1,080 transitions, 5,000 reference cases, 1,560/1,560 injected faults detected, 180 serialisation controls accepted).

The merged revision’s hosted CI, Multiplatform Validation, dependency audit and research workflow passed. A separate adversarial pass reproduced 11 remaining findings through 15 isolated evidence probes; these are documented in the [post-merge audit](docs/ADVERSARIAL_AUDIT_2026_10_26.md). Earlier packaging, research and documentation validation is recorded in [the repair verification](docs/ADVERSARIAL_AUDIT_2026_10_25.md). Historical validation remains in the changelog and pull requests.

## Known limitations and pending work

- Four high-priority audit findings remain: standalone-editor safety bypasses, unguarded queued-turn callbacks after reset, v3 schema/input-validation defects, and missing runtime imports in the extracted research package.
- Medium-priority findings cover temporary-setting persistence, stale context headers, inferred model ownership, overlapping selections, implicit startup downloads, coercion of malformed v2 rules, and unsupported remote-catalogue discovery. See the post-merge audit for evidence and repair order.
- Live Ollama generation and native GUI acceptance have not been run for this audit. Mock HTTP verification does not establish real-model behaviour.
- Native first-run checks on macOS, Linux and Windows, and install-level Apple Silicon Homebrew validation remain release gates.
- Ownership receipts identify BatLLM-launched processes, not per-client model ownership within a shared server. Explicit model deletion/download controls still affect real shared resources.
- Modelito 1.4.6 still has independent lifecycle configuration, unsafe generic shutdown and unbounded CLI helpers. The main facade avoids those entry points, while the standalone editor still reaches them. Remote discovery also relies on unsupported CLI flags; upstream details are in the audit reports.
- v2 analysis is diagnostic and weaker than v3; neither format authenticates a serving binary or model weights.
- Finish the UI consistency and accessibility work in `docs/UI_UNIFICATION_PLAN_1_0.md` before 1.0 sign-off.
- Longer term: separate remaining Kivy coordination, then design the server contract for networked play before adding clients or shared repositories.

Last updated: 2026-10-26 01:19
