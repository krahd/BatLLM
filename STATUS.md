# BatLLM status

Last updated: 2026-11-11 16:35

## Project and release phase

BatLLM is a Python/Kivy research, education and two-player battle game. Human prompts mediate model commands inside a deterministic game world. Version `0.3.6` remains in `0.x` hardening. The published Modelito 1.4.8 migration is merged into `main`; the source baseline is tested, but native UI and download-deadline findings keep stable 1.0 gates unsigned.

## Current capabilities

- Two players, two bots, round prompts, shared or independent conversation histories, and optional game-state prompt augmentation.
- Asynchronous gameplay requests, guarded inference callbacks and guarded scheduled turns; fresh histories for new games and conversation/state rollback for cancelled rounds.
- Strict native Ollama inference through the shared published Modelito 1.4.8 adapter; structured roles, generation options, `stream: false`, explicit deadlines and propagated errors.
- Ollama status, start, warm-up, local inventory, downloads and deletion at BatLLM’s configured endpoint. Shutdown requires an ownership receipt matching endpoint, PID and process creation time; external services remain running.
- Only the latest model selection persists after readiness succeeds; selection never automatically unloads other models. Both management interfaces confirm deletion, unload and download actions. Startup never pulls missing models.
- Remote model-family catalogue discovery uses Modelito at the configured endpoint; failures remain explicit and both interfaces retain confirmed downloads by entered model name.
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
- `src/llm/service.py`: BatLLM configuration, explicit-endpoint management operations and owned-process lifecycle.
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

Urgent audit repairs on 10 November 2026 fixed the prompt-history retrieve crash,
the configurator's first-run placeholder configuration, unsubstituted rule
placeholders and an invalid example in the augmented system instructions, and
the Ollama shell scripts' module path and interpreter selection. A fresh Python
3.12 environment installed from `requirements.txt` passed **337 non-live tests,
2 live tests skipped**, the four-test core preflight, the documentation check and
Pylint at **8.83/10**, including five new Homebrew generator and workflow
checks. The 17 urgent-repair regressions execute both shell scripts up to
argument parsing; 15 of them fail against the previous code. No real Ollama
operation, native GUI rehearsal or `python run_tests.py full` run was performed.

Pre-fork verification on 6 November 2026 used a fresh Python 3.12 environment
installed from `requirements.txt`, including the published Modelito 1.4.8:
**315 non-live tests passed, 2 live tests skipped**, plus the four-test core
preflight. Pylint passed at **8.84/10**; dependency consistency, compilation,
documentation and diff checks passed. The scripted v3 command and verifier ran
from a shell without `KIVY_NO_ARGS`, with **8/8 transitions verified**. No real
Ollama installation, model operation, native GUI rehearsal, or release publication
was performed during this review.

Workshop preparation now selects Python 3.12 explicitly in source-install
commands, documents coordinator/student fork targets and keeps test-owned HTTP
traffic independent of inherited proxies. Research CLI launchers prevent Kivy
from consuming their arguments, and newly built research packages exclude local
poster-capture state. Historical committed artefacts remain unchanged. See
[workshop setup](docs/CONTRIBUTING.md#workshop-forks).

The targeted A1/A2 repairs passed **314 non-live tests, 2 live tests skipped**, the four-test core preflight, Pylint **8.83/10**, compilation and documentation checks. A fresh macOS bundle selected Python **3.12.16** despite a default Python **3.15.2**; both native launchers opened successfully. Physical analyser row selection, preview changes and opening the selected save passed in source and installed-bundle checks at 800×600. Directory navigation and Refresh also passed. See [repair verification](docs/MAIN_AUDIT_2026_10_30.md#targeted-repair-verification--30-october-2026).

The [30 October main audit](docs/MAIN_AUDIT_2026_10_30.md) records results against merged application commit `b1f7d3d` and distinguishes source, live, native and installation acceptance:

- All five post-merge hosted workflows passed, including the Python 3.10–3.12 Linux/macOS/Windows CI matrix, multiplatform validation, dependency audit, research validation and Pages deployment.
- Fresh public Modelito 1.4.8 installation verified; `python run_tests.py full` passed **310 tests with no skips**, following the four-test core preflight. Live smoke used the existing Ollama service with isolated application state and left that external service running.
- Native macOS SDL2 source rehearsal passed one complete game using the shipped two-round/eight-turn length: **32 real `smollm2:latest` plays**. Save, in-app/standalone analyser, replay navigation and compatibility rejection passed through Recent Sessions. Independent traversal of **48 replay positions found zero mismatches**; a tampered control was detected.
- A test-owned Ollama server started, warmed the installed model, established ownership and stopped; the pre-existing external server remained running. No real model download, deletion or explicit unload was performed.
- Compilation, documentation validation and `pip check` passed. Maintained Pylint passed at **8.83/10** with existing warnings. Runtime dependency audit reported no known vulnerabilities at audit time.
- Isolated research experiments passed: 60 sessions, 1,080 equivalent plays, 5,000 reference cases, 1,560/1,560 injected faults detected and 180/180 serialisation controls accepted; the 206-file artefact built successfully.
- Source/platform archive generation, actual formula dependency resolution, and Apple Silicon Homebrew install/test/uninstall passed. The existing bundle installer smoke also returned success, but an additional actual-launch check **failed**: the installer selected unsupported Python 3.15.2. Homebrew GUI launch was not tested.

Earlier evidence remains in the [27 October native rehearsal](docs/NATIVE_REHEARSAL_2026_10_27.md), [26 October adversarial audit](docs/ADVERSARIAL_AUDIT_2026_10_26.md), changelog and merged pull requests. Those historical results are not substitutes for the current audit's explicit limits.

## Known limitations and pending work

- **Homebrew channel not yet published:** `krahd/homebrew-tap` contains no `batllm` formula and the newest repository tag is `v0.3.0`, so the README's `brew install` command cannot succeed until a `v0.3.6` tag is pushed and the publishing workflow runs. The job is restricted to `krahd/BatLLM`, now renders the formula on an Apple Silicon macOS runner, and the generator rejects wheels for other platforms or Python versions. The CI Homebrew dry-run uses the same runner and Python 3.12. On 10 November 2026 the generator rendered a syntactically valid 31-resource formula from the worktree on Apple Silicon macOS; no Homebrew install was run against it, and the workflow itself, the shared token's provider-side scope and its rotation remain unvalidated.

- **A1/A2 repaired:** bundle installers select/check Python 3.10–3.12 and smoke checks validate the installed interpreter; the analyser uses a single custom file-list layout so native row selection works. Windows/Linux native installer acceptance remains unrun.
- **A3 — small-window gameplay:** command headings and footer actions clip/overlap at 800×600. Enlarging the window worked; responsive/minimum-size behaviour needs repair.
- **A4 — download deadline:** management downloads check elapsed time only after an event arrives. A local delayed stream exceeded the requested total timeout. Enforce the remaining deadline during reads and add a partial-progress stall regression.
- Native first-run on Linux/Windows, Homebrew GUI gameplay/save, missing/stopped/unresponsive Ollama UI recovery, actual download/deletion, native malformed-output and damage/fatal-shot paths, exhaustive save/exit/recovery and accessibility remain acceptance work. See the audit for the exact scope.
- User configurations created by the configurator's earlier first-run behaviour may still hold an empty model, a 10-second timeout and a null context size; they are not repaired automatically. Deleting those keys from the user `config.yaml` restores the shipped defaults.
- The non-augmented system-instruction files are empty, so non-augmented games send no command grammar to the model. Whether this is intended remains to confirm.
- Saved v2 sessions do not preserve context/augmentation modes per round or authenticate per-request model identity. v2 analysis is weaker than the v3 research contract; neither authenticates a serving binary or model weights.
- Ownership receipts identify BatLLM-launched processes, not per-client model ownership within a shared server. Explicit model deletion/download controls still affect real shared resources.
- Console cancellation retires UI output immediately and closes its iterator when a fragment or configured read deadline returns; it does not abort a blocked provider read instantly.
- Finish the UI consistency and accessibility work in `docs/UI_UNIFICATION_PLAN_1_0.md` before 1.0 sign-off.
- Longer term: separate remaining Kivy coordination, then design the server contract for networked play before adding clients or shared repositories.

Last updated: 2026-11-11 16:35
