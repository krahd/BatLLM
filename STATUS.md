# BatLLM Status

Last updated: 2026-05-08 20:35

## Project Purpose

BatLLM is a Python/Kivy research, education, and game project focused on AI-mediated gameplay, prompt quality, LLM behaviour, and local-model workflows. The repository provides a playable turn-based app and a read-only analyser for replaying and inspecting saved sessions.

## Setup And Run Instructions

macOS/Linux:

```bash
git clone https://github.com/krahd/BatLLM.git
cd BatLLM
python3 -m venv .venv_BatLLM
source .venv_BatLLM/bin/activate
pip install -r requirements.txt
python run_batllm.py
```

Windows:

```powershell
git clone https://github.com/krahd/BatLLM.git
cd BatLLM
py -m venv .venv_BatLLM
.\.venv_BatLLM\Scripts\Activate.ps1
pip install -r requirements.txt
python run_batllm.py
```

Standalone analyser:

```bash
python run_game_analyzer.py
```

## Current Implementation State

- Main launcher: `run_batllm.py`
- Standalone analyser launcher: `run_game_analyzer.py`
- Source tree under `src/` with Kivy UI, gameplay logic, model orchestration, history, and replay support
- Local Ollama workflow for install/start/stop, model selection, model download/delete
- Saved-session v2 envelope with per-round gameplay snapshots and saved LLM metadata snapshot support
- Cross-platform release-bundle generation and Homebrew packaging support
- Maintained docs in `docs/`

The codebase is currently aligned on `modelito==1.4.0` and now uses structured readiness handling plus configurable warmup timeout in the local Ollama startup path.

## Architecture Overview

- Launchers: `run_batllm.py`, `run_game_analyzer.py`
- Main app entrypoint: `src/main.py`
- LLM/runtime orchestration: `src/llm/service.py`
- Ollama config UI: `src/view/ollama_config_screen.py` and KV layout
- Session export and schema: `src/game/history_manager.py`, `src/game/session_schema.py`
- Analyzer model/inspector UI: `src/analyzer_model.py`, `src/view/analyzer_review_screen.py`
- Tests: `src/tests/`

### Architecture Diagram

![BatLLM architecture](docs/images/architecture-modelito.svg)

### Runtime Flow Diagram

![BatLLM runtime flow](docs/images/request-flow-modelito.svg)

## Important Files And Directories

- `AGENTS.md`: canonical agent instructions for this repository
- `STATUS.md`: complete project status report
- `requirements.txt`: root Python dependency pins
- `packaging/homebrew/requirements.txt`: Homebrew runtime dependency subset
- `src/configs/`: shipped and runtime configuration defaults
- `docs/README.md`, `docs/USER_GUIDE.md`, `docs/CONTRIBUTING.md`: maintained user and developer docs

## Recent Changes

- Warmup timeout wiring completed across config defaults, service CLI, and Ollama config UI.
- Structured readiness path uses `ensure_model_ready_detailed()` and checks `ReadinessResult.success` in UI flows.
- Saved-session payload now includes `llm_metadata`; analyzer now exposes this in a dedicated `Model` inspector tab.
- Focused test coverage added for warmup timeout persistence and readiness success/failure handling.
- Homebrew packaging test collection fixed by ensuring repo-root path bootstrap happens before repo-root imports.
- Root `requirements.txt` now includes `requests==2.32.4` to remain a superset of Homebrew runtime requirements.
- Legacy start/stop UI test updated to match the warmup-timeout argument now passed at service start.
- Repaired a reintroduced import-order regression in `src/tests/test_homebrew_packaging.py` and `src/tests/test_multiplatform_support.py` so pytest collection remains stable.
- Ran packaging smoke validation for release bundles and Homebrew formula generation.
- Hardened the same two test modules to use dynamic post-bootstrap imports so formatter/isort reordering cannot reintroduce collection-time import failures.
- Added `src/util/packaging_smoke.py` plus `validate_packaging_smoke.py` for a unified packaging smoke-validation command.
- Added `src/tests/test_packaging_smoke.py` and contributor docs for the new packaging smoke command.
- Hardened `src/llm/service.py` stop logic so force-kill escalation only applies to Ollama processes that BatLLM has already terminated, reducing the risk of touching unrelated listeners.
- Added targeted regression tests for the stop-service race/kill path in `src/tests/test_multiplatform_support.py`.
- Extended `src/util/packaging_smoke.py` with an opt-in installer smoke mode that extracts the current-platform release bundle, executes `install-batllm.*`, and verifies the expected `.venv_BatLLM` Python executable.
- Added installer-smoke helper coverage in `src/tests/test_packaging_smoke.py`.
- Documented the installer smoke command path in `docs/CONTRIBUTING.md`.
- Added an opt-in Homebrew install-level smoke mode in `src/util/packaging_smoke.py` that performs install/test/uninstall through a temporary local tap, compatible with current Homebrew policy.
- Updated `docs/CONTRIBUTING.md` and `packaging/homebrew/README.md` to document the local-tap requirement for Homebrew install smoke.
- Regenerated generated API docs under `docs/code/` with `doxygen docs/code/dox_config.properties`.
- Narrowed `src/llm/service.py` startup orchestration by delegating the no-config path directly to `modelito.start_service()` instead of falling back to the local startup branch.
- Added regression coverage in `src/tests/test_multiplatform_support.py` for the no-config startup delegation path.
- Narrowed default-path service-state orchestration by delegating `inspect_service_state(None)` directly to `modelito.inspect_service_state(None)`.
- Hardened Homebrew install smoke to report a clear error when `brew` is unavailable on `PATH`.
- Added regression coverage for the new service-state delegation path and missing-`brew` handling.
- Ran a comprehensive repository audit pass across working tree state, core documentation, source and packaging scripts, and automated verification commands.
- Updated `docs/code/dox_config.properties` `PROJECT_NUMBER` from `0.2.3` to `0.3.4` and regenerated `docs/code/` so generated API docs match the current repository version.
- Fixed `run_tests.py` import-order and module-resolution issues so `python run_tests.py full` now works from the repository root without ad-hoc `PYTHONPATH` setup.
- Completed the live-Ollama gated smoke next step via `python run_tests.py full`.
- Replaced home-screen overlay TODO markers with an explicit rationale so the workaround is documented and tracked without ambiguous TODO debt.
- Removed debug-only prompt-history prints from `src/view/home_screen.py`.
- Updated `docs/UI_UNIFICATION_PLAN_1_0.md` with explicit 1.0 status per workstream (done versus deferred to 1.1).
- Added `v1.0.0` release notes in `docs/CHANGELOG.md` and reset `Unreleased` to an empty placeholder.
- Bumped repository version metadata to `1.0.0` (`VERSION`, Doxygen `PROJECT_NUMBER`) and regenerated `docs/code/`.
- Fixed import-order regressions in all three root entry scripts (`run_batllm.py`, `run_game_analyzer.py`, `run_tests.py`) by inserting `src/` on `sys.path` before importing `util.compat`.
- Enabled GitHub branch protection on `main` with required checks (`Multiplatform Validation / test`, `Multiplatform Validation / homebrew`, `Multiplatform Validation / smoke`), strict up-to-date enforcement, required conversation resolution, and one required approving review.
- Bumped repository version metadata back to `0.3.5` so the project remains on the `0.x` line pending maintainer testing.
- Made explicit-platform install-command resolution deterministic in `src/llm/service.py` while preserving modelito delegation for runtime auto-detection.
- Repaired reintroduced import-order regressions in the root launchers (`run_batllm.py`, `run_game_analyzer.py`, `run_tests.py`) so `src/` path bootstrap happens before importing `util.compat`.
- Updated `.github/workflows/multiplatform.yml` Homebrew job environment to use the same headless Kivy/PYTHONPATH settings as other CI jobs.
- Relaxed `src/tests/smoke_llm_payload.py` health-check assertion for mock-only CI runs where service state can be running with `installed=False` and an empty version string.

## Tests And Verification Status

Executed in this work session:

- `pytest -q src/tests/test_ollama_config_screen_logic.py src/tests/test_multiplatform_support.py src/tests/test_game_analyzer.py` -> `57 passed`
- `pytest -q src/tests/test_homebrew_packaging.py` -> `7 passed`
- `pytest -q` -> `138 passed, 2 skipped`
- `python create_release_bundles.py` -> generated all expected archives under `dist/releases/`.
- `python create_homebrew_formula.py --create-worktree-archive /tmp/BatLLM-homebrew-source.tar.gz --formula-out /tmp/batllm.rb` -> completed successfully and wrote `/tmp/batllm.rb`.
- `pytest -q src/tests/test_packaging_smoke.py` -> `4 passed`
- `python validate_packaging_smoke.py --skip-homebrew` -> `Packaging smoke validation passed.`
- `python validate_packaging_smoke.py` -> `Packaging smoke validation passed.`
- `pytest -q` -> `142 passed, 2 skipped`
- `pytest -q src/tests/test_multiplatform_support.py` -> `29 passed`
- `pytest -q src/tests/test_packaging_smoke.py src/tests/test_multiplatform_support.py` -> `36 passed`
- `python validate_packaging_smoke.py --run-installer-smoke` -> `Packaging smoke validation passed.`
- `python create_homebrew_formula.py --create-worktree-archive /tmp/BatLLM-homebrew-source.tar.gz --formula-out /tmp/batllm.rb && brew install/test/uninstall via temporary local tap` -> completed successfully.
- `pytest -q src/tests/test_packaging_smoke.py src/tests/test_multiplatform_support.py` -> `37 passed`
- `python validate_packaging_smoke.py --skip-release-bundles --skip-homebrew --run-homebrew-install-smoke --homebrew-install-timeout 1800` -> `Packaging smoke validation passed.`
- `doxygen docs/code/dox_config.properties` -> completed successfully; regenerated `docs/code/` HTML/LaTeX outputs.
- `pytest -q src/tests/test_multiplatform_support.py src/tests/test_packaging_smoke.py` -> `38 passed`
- `pytest -q` -> `149 passed, 2 skipped`
- `pytest -q src/tests/test_multiplatform_support.py src/tests/test_packaging_smoke.py` -> `40 passed`
- `pytest -q` -> `151 passed, 2 skipped`
- `pytest -q src/tests/test_homebrew_packaging.py src/tests/test_packaging_smoke.py` -> `16 passed`
- `python -m py_compile run_batllm.py run_game_analyzer.py run_tests.py create_release_bundles.py create_homebrew_formula.py validate_packaging_smoke.py src/llm/service.py src/util/packaging_smoke.py` -> completed successfully (no syntax errors)
- `doxygen docs/code/dox_config.properties` -> completed successfully after updating `PROJECT_NUMBER` to `0.3.4`
- `python run_tests.py full` -> core smoke `4 passed`; full suite with live-Ollama gating `153 passed`; runner successfully started and stopped local Ollama through `llm.service`.
- `/Users/tom/devel/ml-llm/llm/BatLLM/.venv_BatLLM/bin/python create_release_bundles.py` -> generated source and platform release archives under `dist/releases/`.
- `/Users/tom/devel/ml-llm/llm/BatLLM/.venv_BatLLM/bin/python create_homebrew_formula.py --create-worktree-archive /tmp/BatLLM-homebrew-source.tar.gz --formula-out /tmp/batllm.rb` -> completed successfully and wrote `/tmp/batllm.rb`.
- `/Users/tom/devel/ml-llm/llm/BatLLM/.venv_BatLLM/bin/python -m pytest -q src/tests/test_homebrew_packaging.py` -> `7 passed`.
- `/Users/tom/devel/ml-llm/llm/BatLLM/.venv_BatLLM/bin/python run_tests.py full` -> core smoke `4 passed`; full suite `153 passed`; live-Ollama lifecycle start/stop verified.
- `/Users/tom/devel/ml-llm/llm/BatLLM/.venv_BatLLM/bin/python -m pytest -q` -> `151 passed, 2 skipped`.
- `doxygen docs/code/dox_config.properties` -> completed successfully with `DOXYGEN_EXIT:0`; regenerated HTML/LaTeX docs for version `0.3.5`.
- `gh api -X PUT repos/krahd/BatLLM/branches/main/protection --input ...` -> completed successfully; protection now enforces required checks and review policy on `main`.
- `gh api repos/krahd/BatLLM/branches/main/protection` -> completed successfully; verified active protection settings.
- `/Users/tom/devel/ml-llm/llm/BatLLM/.venv_BatLLM/bin/python -m pytest -q src/tests/test_multiplatform_support.py::test_install_command_for_current_platform_is_platform_specific src/tests/test_ollama_config_screen_logic.py::test_build_ollama_install_command_is_platform_specific src/tests/test_homebrew_packaging.py` -> `9 passed`.
- `/Users/tom/devel/ml-llm/llm/BatLLM/.venv_BatLLM/bin/python -m py_compile run_batllm.py run_game_analyzer.py run_tests.py src/llm/service.py` -> completed successfully (no syntax errors).

## Known Issues, Risks, And Limitations

- `src/llm/service.py` still owns BatLLM-specific overlay logic and timeout policy; avoid re-expanding it into a generic provider abstraction already handled by `modelito`.
- Homebrew install-level smoke now depends on temporary local tap setup because current Homebrew rejects direct file-based formula installs outside a tap.
- First-run checklist execution is complete for command-level macOS validation but still requires manual Linux and Windows first-run pass/sign-off.

## Recurring Tasks

- Keep hygiene checks current as packaging and release scripts evolve.
- Keep STATUS and maintained docs aligned with any additional runtime or packaging changes.
- Keep maintenance-level monitoring in place for future `modelito` and Homebrew policy changes.

## Pending Tasks

- Complete manual first-run checklist execution on Linux and Windows hosts and update `docs/FIRST_RUN_RELEASE_CHECKLIST.md` sign-off to fully complete.
- Final maintainer release actions: freeze scope on release branch, rerun required CI checks, and tag a `0.x` release candidate (`v0.3.5`) when external gates are complete.

## Next Steps — Remaining Before Tagging v0.3.5

Implemented from the previous cycle in this session:

1. Criterion 3 UX gaps addressed for 1.0 tracking: overlay workaround documented, debug print removed, and UI unification workstreams marked done/deferred in `docs/UI_UNIFICATION_PLAN_1_0.md`.
2. Criterion 5 documentation/versioning addressed: draft `v1.0.0` notes are kept as non-released reference only; active repository versioning is `0.3.5`; Doxygen metadata and generated API docs are aligned to `0.3.5`.
3. Release-signoff command set executed locally: release bundles built, Homebrew formula rendered, Homebrew packaging tests passed, full test suite and `run_tests.py full` passed.
4. Criterion 1 branch-protection gate completed: required checks and review/conversation rules are now enforced on `main`.

Remaining external maintainer actions (not fully automatable from this workspace):

1. Complete Linux and Windows manual first-run checklist execution and finalise checklist sign-off as complete.
2. Perform final release branch freeze/tag workflow (`v0.3.5`) once the manual platform sign-offs are complete.

## Longer-Term Steps

1. Decide GUI direction for web-app surface versus Kivy-only roadmap. Analysis: this is the highest-leverage product decision because multiplayer, prompt sharing, and deployment choices all depend on whether Kivy remains the only client. Kivy and a web surface can coexist, but the added complexity yields no clear gain before 1.0. Decision: defer a web surface until after 1.0; revisit only if cross-device or teacher-mode use cases demand it. Comparable projects (Jan, GPT4All) gained traction without a web surface first.
2. LAN multiplayer support. Analysis: best first networking milestone; deterministic replay must be preserved by introducing an authoritative turn-order protocol and a schema-stable, versioned event log before any socket code is written. The replay schema must be frozen (versioned and migration-tested) as a hard precondition — any multiplayer session that references an unstable schema is fragile. Multiplayer will also require new GUI modes.
3. Internet multiplayer support. Analysis: should follow LAN once identity, matchmaking, and anti-abuse controls are defined. Additional precondition not in earlier steps: once strangers can play together, prompt injection into the LLM path becomes a meaningful attack surface and must be explicitly scoped and mitigated before public exposure.
4. Prompt library/repository and examples. Analysis: the session schema/version governance precondition remains correct, but this item is strategically more important than its position implies. A shared prompt library is the primary educational centrepiece of the project — the mechanism by which players compare model behaviours across scenarios. Promptfoo, DeepEval, and Langfuse build their community value around shared test cases; BatLLM's equivalent is game-framed prompts. Schema stability is a precondition, not the goal.
5. Additional computer-controlled player modes. Analysis: lowest infrastructure risk; can progress in parallel with 1.x maintenance. Educational value is higher than it appears: distinct bot personalities (aggressive, defensive, random, rules-only) give players a direct way to observe and compare model behavioural differences, which ties directly to the core learning loop. GUI impact is manageable within the existing screen structure.
6. Experiment/Evaluation Mode. Analysis: batch-run scenarios with fixed seeds across model and prompt configurations and produce a scored outcome log. This is the highest-differentiating capability BatLLM could offer that no comparable project provides in a game context. A scoped first version is achievable before 1.0 because seed-based replay and outcome logging are already partially implied by the existing replay engine. Precondition: deterministic seed propagation must be verified across the full game loop.
7. GUI improvements and redesigns (two separate tracks). Track A — incremental polish: can happen continuously within the 1.x cycle without a discrete decision point. Track B — UI/UX redesign: a discrete strategic decision, best deferred to 1.1 alongside any webapp or multiplayer work. A reasonable sequencing is: reach 1.0 with Kivy-only, polished incrementally; then plan 1.1 around a unified rethink of UI/UX, webapp surface, and multiplayer simultaneously.

---

Last updated: 2026-05-08 20:35
