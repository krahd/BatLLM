# BatLLM status

Last updated: 2026-10-27 15:40

## Project and release phase

BatLLM is a Python/Kivy research, education and two-player battle game. Human prompts mediate model commands inside a deterministic game world. Version `0.3.6` remains in `0.x` hardening; stable 1.0 gates are unsigned.

## Current capabilities

- Two players, two bots, round prompts, shared or independent conversation histories, and optional game-state prompt augmentation.
- Asynchronous gameplay requests, guarded inference callbacks and guarded scheduled turns; fresh histories for new games and conversation/state rollback for cancelled rounds.
- Strict native Ollama inference through the shared Modelito 1.4.6 adapter; structured roles, generation options, `stream: false`, explicit deadlines and propagated errors.
- Ollama status, start, warm-up, local inventory, downloads and deletion at BatLLM’s configured endpoint. Shutdown requires an ownership receipt matching endpoint, PID and process creation time; external services remain running.
- Only the latest model selection persists after readiness succeeds; selection never automatically unloads other models. Both management interfaces confirm deletion, unload and download actions. Startup never pulls missing models.
- Unsupported remote-catalogue discovery is reported explicitly; both interfaces support confirmed downloads by entered model name.
- Atomic configuration and session persistence. Session-v2 exports contain completed turns, frozen rules and a configuration metadata snapshot, without live metadata queries during saving.
- Game Analyzer validates action records and replay states, and flags response–command disagreement and turn-continuity breaks.
- Headless schema-v3 research runtime and verifier use the committed JSON Schema before semantic checks and preserve application-level invocation evidence, grounding, replay and semantic-event checks. This does not authenticate model execution or historical traces.

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
- `src/configs/app_config.py`: section-validated loading, execution-only setting overrides and atomic preference writes.
- `src/configs/configurator.py`: standalone editor using the same strict transport and explicit-endpoint management operations.
- `src/util/paths.py`: resources, user state and legacy-session copying.
- `src/view/` and `src/analyzer_model.py`: Kivy screens and analyser presentation.
- `create_release_bundles.py`: full source archives and smaller platform runtime bundles; research packaging is separate.
- `research/urucon2026/`: implementation-owned corpus, results, schema, claims and reproducibility package. The editable paper remains in `krahd/academic-writing`.
- `.github/workflows/`: platform, dependency, research and release checks, with actions pinned by commit.
- `README.md`, `docs/USER_GUIDE.md`, `docs/CONTRIBUTING.md` and `docs/RELEASE_CRITERIA_1_0.md`: public, user, developer and release references.

## Configuration and mutable state

Shipped defaults in `src/configs/config.yaml` are read-only. Preferences and relative session directories use `BATLLM_HOME` when set, otherwise the platform user data directory. Legacy checkout JSON sessions are copied on default-directory access without moving originals or overwriting existing files. Absolute session paths retain their meaning. See [state and installation](docs/STATE_AND_INSTALLATION.md).

Both management interfaces use explicit BatLLM endpoints and the guarded service facade. Temporary game/UI settings are excluded from incidental preference saves. Ownership receipts are stored in the user directory, allowing a helper subprocess to start a service that the application can later stop safely.

## Validation evidence

Current local Python 3.12/macOS validation:

- current isolated non-live suite: `304 passed, 2 skipped`; focused analyser/Ollama screens: `67 passed` (27 October 2026). The earlier pre-repair rehearsal passed `293` tests with real-Ollama smoke enabled; live smoke was not repeated for these UI repairs;
- native source rehearsal: two complete games, four rounds, eight turns and sixteen real `smollm2:latest` responses; native save/save-on-exit and in-app/standalone analyser load, navigation, compatibility rejection and mismatch diagnosis passed; independent traversal of all 24 saved replay positions found zero mismatches; see [native rehearsal audit](docs/NATIVE_REHEARSAL_2026_10_27.md);
- native repair checks: clear/scrollable previews at 1440×900, 1024×768 and 800×600 logical sizes; file-list addition/removal and retained selection passed through scheduled native UI events; the original save checksum and all 24 replay positions reverified;
- maintained regressions cover all eleven earlier audit findings and the new Refresh/alias cases, including standalone endpoint/deadline/confirmation boundaries, cancellation, reset races, temporary settings, context changes, stale selections, imported rules and malformed v3 traces;
- extracted research ZIP generates and verifies scripted traces with the original checkout absent from the subprocess import path;
- full Pylint gate: passed, `8.84/10`, no errors; existing warnings remain;
- compilation, documentation validation, KV parsing and diff checks: passed;
- Homebrew formula generation with actual dependency resolution/hashes: passed; `jsonschema` is now a runtime dependency;
- isolated research pipeline and package build: passed (60 traces, 1,080 transitions, 5,000 reference cases, 1,560/1,560 injected faults detected and 180 serialisation controls accepted).

The [post-merge audit](docs/ADVERSARIAL_AUDIT_2026_10_26.md) retains the original `d86ae05` evidence and a separate current repair disposition. PR #65 remains stacked on unmerged PR #63. Its new repair commit has not run the protected-main workflow matrix; prior hosted repair-branch checks are tracked in PR #63. Historical repair evidence remains in [the first audit verification](docs/ADVERSARIAL_AUDIT_2026_10_25.md), the changelog and pull requests.

## Known limitations and pending work

- The three native-audit usability defects are repaired: bounded/scrollable previews, both file lists refreshed and omitted-tag model status corrected. Native error/recovery and damage/exit combinations remain partially untested; see the native audit for exact scope.
- Saved v2 sessions do not preserve context/augmentation modes per round or authenticate per-request model identity; use the research trace contract for research evidence.
- Native first-run checks on macOS, Linux and Windows, and install-level Apple Silicon Homebrew validation remain release gates.
- Ownership receipts identify BatLLM-launched processes, not per-client model ownership within a shared server. Explicit model deletion/download controls still affect real shared resources.
- Modelito 1.4.6 retains unsupported automatic catalogue discovery and generic lifecycle/deadline limitations. BatLLM avoids those paths and offers manual model-name download recovery; upstream details remain in the audit reports.
- Console cancellation retires UI output immediately and closes its iterator when a fragment or configured read deadline returns; it does not abort a blocked provider read instantly.
- v2 analysis is diagnostic and weaker than v3; neither format authenticates a serving binary or model weights.
- Finish the UI consistency and accessibility work in `docs/UI_UNIFICATION_PLAN_1_0.md` before 1.0 sign-off.
- Longer term: separate remaining Kivy coordination, then design the server contract for networked play before adding clients or shared repositories.

Last updated: 2026-10-27 15:40
