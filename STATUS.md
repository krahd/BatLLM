# BatLLM Status

Last updated: 2026-05-09 14:13

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

- Release-preparation work is functionally complete for the automatable path: release bundles build, Homebrew formula generation works, and packaging smoke validation passes.
- The repository remains on version `0.3.5`; the earlier `1.0.0` notes are retained only as draft reference material and are not the active release line.
- Root launchers and `run_tests.py` were stabilised so repository-root execution works without ad-hoc `PYTHONPATH` setup.
- `src/llm/service.py` now keeps explicit install-command mapping deterministic for tests while preserving modelito runtime auto-detection when no platform override is supplied.
- `.github/workflows/multiplatform.yml` is aligned with the Homebrew dry-run job's headless Kivy/PYTHONPATH requirements.
- Mock-Ollama smoke coverage now tolerates the expected CI state where the service can be reachable with `installed=False` and no version string.
- GitHub branch protection on `main` now uses the live required check names published by GitHub Actions: `ubuntu-latest`, `windows-latest`, `macos-latest`, `Homebrew dry-run`, and `Smoke: Ollama integration`.
- Maintained release documents were updated to reflect the current `0.x` hold pending manual maintainer sign-off.

## Tests And Verification Status

Recent verified commands:

- `python run_tests.py full` -> core smoke `4 passed`; full suite `153 passed`; live-Ollama lifecycle start/stop verified.
- `pytest -q` -> `151 passed, 2 skipped`.
- `pytest -q src/tests/test_homebrew_packaging.py` -> `7 passed`.
- `pytest -q src/tests/test_multiplatform_support.py::test_install_command_for_current_platform_is_platform_specific src/tests/test_ollama_config_screen_logic.py::test_build_ollama_install_command_is_platform_specific src/tests/test_homebrew_packaging.py` -> `9 passed`.
- `python create_release_bundles.py` -> generated expected platform and source archives under `dist/releases/`.
- `python create_homebrew_formula.py --create-worktree-archive /tmp/BatLLM-homebrew-source.tar.gz --formula-out /tmp/batllm.rb` -> completed successfully and wrote `/tmp/batllm.rb`.
- `python validate_packaging_smoke.py` -> `Packaging smoke validation passed.`
- `python validate_packaging_smoke.py --run-installer-smoke` -> `Packaging smoke validation passed.`
- `python validate_packaging_smoke.py --skip-release-bundles --skip-homebrew --run-homebrew-install-smoke --homebrew-install-timeout 1800` -> `Packaging smoke validation passed.`
- `python -m py_compile run_batllm.py run_game_analyzer.py run_tests.py create_release_bundles.py create_homebrew_formula.py validate_packaging_smoke.py src/llm/service.py src/util/packaging_smoke.py` -> completed successfully (no syntax errors).
- `doxygen docs/code/dox_config.properties` -> completed successfully; generated docs align with version `0.3.5`.
- `gh api repos/krahd/BatLLM/branches/main/protection` -> verified the live required-check configuration on `main`.

This PR is documentation-only; no additional code execution was required for the STATUS sanitisation itself.

## Known Issues, Risks, And Limitations

- `src/llm/service.py` still owns BatLLM-specific overlay logic and timeout policy; avoid re-expanding it into a generic provider abstraction already handled by `modelito`.
- Homebrew install-level smoke depends on temporary local tap setup because current Homebrew rejects direct file-based formula installs outside a tap.
- First-run checklist execution is complete for command-level macOS validation but still requires manual Linux and Windows first-run pass/sign-off.

## Recurring Tasks

- Keep hygiene checks current as packaging and release scripts evolve.
- Keep STATUS and maintained docs aligned with any additional runtime or packaging changes.
- Keep maintenance-level monitoring in place for future `modelito` and Homebrew policy changes.

## Pending Tasks

- Complete manual first-run checklist execution on Linux and Windows hosts and update `docs/FIRST_RUN_RELEASE_CHECKLIST.md` sign-off to fully complete.
- Final maintainer release actions: freeze scope on a release branch, rerun required CI checks, and tag `v0.3.5` only after the manual platform sign-offs are complete.

## Next Steps — Remaining Before Tagging v0.3.5

Automatable release-preparation work already completed:

1. Release-bundle creation, Homebrew formula rendering, packaging smoke checks, and full automated test coverage have been exercised successfully.
2. Active repository versioning, Doxygen metadata, and maintained release documents are aligned on `0.3.5` rather than a `1.0` tag.
3. Branch protection on `main` now uses the live GitHub Actions check names and strict up-to-date enforcement.
4. Launcher, runtime-install, and mock-smoke regressions identified during CI review have been fixed and revalidated.

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

Last updated: 2026-05-09 14:13
