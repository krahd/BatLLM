# BatLLM Status

Last updated: 2026-05-09 20:46

## Project Purpose

BatLLM is a Python/Kivy research, education, and game project for exploring AI-mediated play, prompt quality, LLM behaviour, and local-model workflows. The repository currently contains a playable local desktop game, a standalone read-only Game Analyzer, local Ollama lifecycle and model-management helpers routed through `modelito`, release-bundle tooling, Homebrew formula generation, generated API reference artefacts, and maintained user/developer documentation.

The project should remain practical, critical, and educational. Destructive or expensive local-model actions must stay explicit because BatLLM can start and stop a real Ollama service, download or delete models, and save user-created sessions.

## Setup And Run Instructions

### Supported Runtime

- Python: `>=3.10` and `<3.13` enforced by the launcher compatibility helper.
- Main UI framework: Kivy `2.3.1` plus KivyMD `1.2.0`.
- LLM/runtime integration: Ollama through `modelito==1.4.0` and `ollama==0.5.3`.
- Default shipped model: `smollm2` with first-run `last_served_model` intentionally blank.
- Repository version: `0.3.5`.

### macOS/Linux

```bash
git clone https://github.com/krahd/BatLLM.git
cd BatLLM
python3 -m venv .venv_BatLLM
source .venv_BatLLM/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python run_batllm.py
```

### Windows PowerShell

```powershell
git clone https://github.com/krahd/BatLLM.git
cd BatLLM
py -m venv .venv_BatLLM
.\.venv_BatLLM\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python run_batllm.py
```

### Standalone Game Analyzer

```bash
python run_game_analyzer.py
```

### Test Runner

```bash
python -m pytest -q
python run_tests.py core
python run_tests.py full
```

`run_tests.py full` requires `.venv_BatLLM` and may start/stop a real local Ollama service. Use it only when local Ollama state is safe to exercise.

### Useful Environment Variables

- `BATLLM_HOME`: redirects mutable config and saved-session data away from the repository or package install location.
- `PYTHONPATH=src`: needed when running modules directly without the root launchers.
- `KIVY_WINDOW=mock`, `KIVY_NO_ARGS=1`, `KIVY_NO_CONSOLELOG=1`: useful for headless CI/test runs.
- `BATLLM_RUN_OLLAMA_SMOKE=1`: enables gated Ollama smoke tests.

## Thorough Audit Snapshot

This status update followed a repository-wide audit on 2026-05-09. The audit inspected tracked files, top-level project structure, maintained documentation, source modules, tests, packaging tools, CI workflows, configuration defaults, generated documentation artefacts, and current git state.

### Repository Inventory

- Tracked files: 611.
- Tracked source/test/application files under `src/`: 82.
- Tracked documentation files and generated API artefacts under `docs/`: 505.
- Test files: 13 `test_*.py` files with 153 collected test functions by static scan.
- Key top-level launchers and tooling: `run_batllm.py`, `run_game_analyzer.py`, `run_tests.py`, `create_release_bundles.py`, `create_homebrew_formula.py`, `validate_packaging_smoke.py`, `start_ollama.sh`, `stop_ollama.sh`, `scripts/cmr-r`, and `tools/ollama_mock_server.py`.
- CI workflows present: `.github/workflows/multiplatform.yml` and `.github/workflows/publish-homebrew-tap.yml`.
- Packaging subtree present: `packaging/homebrew/README.md` and `packaging/homebrew/requirements.txt`.

### Notable Audit Findings

- `STATUS.md` now embeds architecture and runtime diagrams via repository SVG image links for markdown-renderer compatibility.
- Removed tracked repository-hygiene artefacts: top-level `sdf` and `src/configs/config.yaml.bak`.
- Fixed stale augmented system-instruction paths in `src/configs/config-llama.yaml` to use `src/assets/system_instructions/...`.
- Removed the unused `OLLAMA_HELPER` constant from `run_tests.py`.
- Refreshed `docs/ROADMAP.md` opening wording from `0.2.x` to `0.3.x`.
- Updated standalone `docs/images/*modelito.svg` wording to retire stale `modelito 1.2.2` references.
- Generated Doxygen output under `docs/code/` is large and tracked. It appears intentional, but it dominates repository size and should be regenerated only as part of deliberate API-documentation updates.
- The current git worktree was clean before this status update.

## Current Implementation State

### Main Application

- `run_batllm.py` bootstraps `src/` onto `sys.path`, enforces the supported Python range, imports `main.main`, and starts the desktop app.
- `src/main.py` builds the KivyMD application, registers Kivy resource paths, loads KV screens, manages the screen manager, handles startup Ollama flow, and supports guarded shutdown behaviour.
- `src/view/home_screen.py`, `src/view/settings_screen.py`, `src/view/history_screen.py`, and `src/view/ollama_config_screen.py` provide the main gameplay, settings, history, and model-management screens.
- `src/game/game_board.py`, `src/game/bot.py`, and `src/game/bullet.py` implement the live arena, bots, movement, shooting, shields, turns, rounds, and rendering behaviour.
- `src/game/ollama_connector.py` manages per-bot/shared prompt history, builds modelito-compatible messages, resolves request options, invokes the LLM provider, and handles timeout errors.

### Game Analyzer

- `run_game_analyzer.py` bootstraps `src/`, enforces Python compatibility, imports `analyzer_main.main`, and starts the standalone analyzer.
- `src/analyzer_main.py` provides the KivyMD analyzer app shell.
- `src/analyzer_model.py` loads validated saved-session payloads and exposes game/round/turn navigation data.
- `src/view/analyzer_load_screen.py`, `src/view/analyzer_review_screen.py`, and `src/view/analyzer_board.py` provide recent-session loading, replay navigation, read-only board rendering, metadata inspection, and playback controls.

### Session, History, And Replay

- `src/game/history_manager.py` records games, rounds, turns, prompt/response histories, state snapshots, winners, and saved-session exports.
- `src/game/session_schema.py` builds and validates the saved-session v2 envelope and rejects unsupported legacy sessions.
- `src/game/replay_engine.py` is a pure replay helper layer used by both gameplay tests and the analyzer. It normalises bot state, parses commands, applies movement/rotation/shooting, resolves shots, and compares replayed state with captured state.
- Saved sessions include gameplay settings snapshots and LLM metadata snapshots so analyzer review can explain the model/runtime context used by a session.

### Configuration And Mutable State

- `src/configs/config.yaml` is the shipped default configuration.
- `src/configs/app_config.py` loads hard-coded defaults, overlays shipped config, and optionally overlays a mutable user config resolved through `BATLLM_HOME`.
- `src/util/paths.py` centralises repository paths, asset/view paths, user-writable `BATLLM_HOME` paths, and saved-session directory resolution.
- `src/configs/configurator.py` is a separate Kivy configuration GUI with YAML editing, snapshots, Ollama controls, model utilities, and a console panel. It is present but not wired through the main root launcher.

### Ollama And Modelito Integration

- `src/llm/service.py` is the central facade over `modelito.ollama_service` and `modelito.providers.ollama`.
- The facade handles config loading, endpoint construction, service state inspection, local model listing, remote model listing, downloads, deletes, start/stop, warm-up, timeout resolution, common model timeout defaults, metadata snapshots, and CLI lifecycle commands.
- The Ollama config screen uses structured readiness results and configurable warm-up timeout to report startup phases and errors more clearly.
- Homebrew packaging intentionally keeps mutable config and saved sessions outside the install cellar by using `BATLLM_HOME`.

### Packaging And Release Tooling

- `create_release_bundles.py` creates versioned source and platform archives under `dist/releases/`.
- `create_homebrew_formula.py` renders a source-based `batllm` formula, supports worktree archive generation, and can target tags or branches.
- `src/util/packaging_smoke.py` and `validate_packaging_smoke.py` validate expected release artefacts, required launcher members, and optional installer/Homebrew smoke paths.
- `.github/workflows/multiplatform.yml` runs Linux, Windows, and macOS tests/build checks, a Homebrew dry run, and mock-Ollama smoke coverage.
- `.github/workflows/publish-homebrew-tap.yml` publishes the formula to `krahd/homebrew-tap` for version tags or manual dispatch when `HOMEBREW_TAP_TOKEN` is configured.

## Architecture Overview

### Architecture Diagram

![BatLLM architecture](docs/images/architecture-modelito.svg)

### Runtime Flow Diagram

![BatLLM runtime flow](docs/images/request-flow-modelito.svg)

## Important Files And Directories

- `AGENTS.md`: canonical operating instructions for coding agents in this repository.
- `STATUS.md`: this complete project status report; must be updated with any project-state change.
- `VERSION`: active repository version (`0.3.5`).
- `requirements.txt`: root development/runtime dependency pins.
- `pytest.ini`: pytest path and discovery configuration.
- `.github/workflows/`: CI and Homebrew tap publication workflows.
- `run_batllm.py`: main application launcher.
- `run_game_analyzer.py`: standalone Game Analyzer launcher.
- `run_tests.py`: cross-platform core/full test runner.
- `src/`: application, game, analyzer, utility, and test source.
- `src/app.kv` and `src/view/*.kv`: Kivy layout definitions.
- `src/assets/`: images, prompts, sounds, and system instructions.
- `src/configs/`: shipped/default config, alternate config, app config loader, and configurator GUI.
- `src/game/`: live game state, bot/bullet primitives, history, LLM connector, replay engine, and session schema.
- `src/llm/service.py`: central Ollama/modelito service facade.
- `src/tests/`: automated tests and smoke helpers.
- `src/util/`: compatibility, path, packaging-smoke, version, and UI utility helpers.
- `src/view/`: Kivy screen classes and UI helpers.
- `docs/`: maintained user/developer docs, screenshots, diagrams, and generated API docs.
- `packaging/homebrew/`: Homebrew distribution docs and pinned formula requirements.
- `tools/ollama_mock_server.py`: local mock server for Ollama integration smoke tests.

## Documentation State

- `docs/README.md` is the canonical project overview and includes setup, Homebrew install notes, concepts, compatibility, troubleshooting, and glossary material.
- `docs/USER_GUIDE.md` is the user-facing manual for gameplay, commands, screens, settings, analyzer use, sessions, and troubleshooting.
- `docs/CONTRIBUTING.md` is the developer manual for setup, architecture, tests, release workflow, docs workflow, coding conventions, and troubleshooting.
- `docs/ROADMAP.md` describes 1.0 local desktop hardening and 2.0 networked-play direction using current `0.3.x` line wording.
- `docs/RELEASE_CRITERIA_1_0.md` defines CI, reliability, UX, bundle, and documentation gates for a future 1.0 candidate.
- `docs/CHANGELOG.md` keeps active unreleased notes on the `0.x` hold and draft 1.0 notes.
- `docs/FIRST_RUN_RELEASE_CHECKLIST.md` and `docs/UI_UNIFICATION_PLAN_1_0.md` remain release-preparation references.
- `docs/code/` contains generated Doxygen HTML/LaTeX output and should be treated as generated documentation.

## Tests And Verification Status

### Latest Commands Run For This Audit

- `pwd && rg --files -g 'AGENTS.md' -g '!**/.git/**' -g '!**/__pycache__/**' && git status --short` -> passed; confirmed repository path, only root `AGENTS.md`, and initially clean worktree.
- `find . -maxdepth 2 -type f ...` plus `rg --files -g '*.py' ...` -> passed; inventoried top-level files and Python files.
- Documentation/source inspection commands using `sed`, `find`, `git ls-files`, and AST parsing -> passed; informed this status report.
- `rg '^def test_' src/tests -c | awk ...` -> passed; statically counted 153 test functions across 13 test files.
- `python -m pytest -q` -> failed during collection in this container because the default `python` is Python 3.14.4 and does not have required dependencies installed (`ModuleNotFoundError: No module named 'yaml'`).
- `python3.12 -m compileall -q src run_batllm.py run_game_analyzer.py run_tests.py create_release_bundles.py create_homebrew_formula.py validate_packaging_smoke.py` -> passed; source and launcher files compile under Python 3.12.
- `python - <<'PY' ...` timestamp-format check -> passed; top and bottom `Last updated` lines match and use the required format.

### Recent Previously Recorded Validation

The previous status report recorded these successful checks from the same release-hardening period. They remain useful historical evidence but were not rerun as part of this documentation-only audit unless listed above.

- `python -m pytest -q` -> `151 passed, 2 skipped`.
- `python run_tests.py full` -> core smoke `4 passed`; full suite `153 passed`; live-Ollama lifecycle start/stop verified.
- `python create_release_bundles.py` -> generated expected `BatLLM-v0.3.5` source and platform archives under `dist/releases/`.
- `python create_homebrew_formula.py --create-worktree-archive /tmp/BatLLM-homebrew-source.tar.gz --formula-out /tmp/batllm.rb` -> completed successfully.
- `python -m pytest -q src/tests/test_homebrew_packaging.py` -> `7 passed`.
- `python validate_packaging_smoke.py` -> `Packaging smoke validation passed.`
- GitHub branch-protection API check previously confirmed required check names: `ubuntu-latest`, `windows-latest`, `macos-latest`, `Homebrew dry-run`, and `Smoke: Ollama integration`.

### Validation Not Run In This Audit

- The Kivy desktop app was not launched interactively with `python run_batllm.py` in this non-interactive environment.
- The standalone analyzer was not launched interactively with `python run_game_analyzer.py` in this non-interactive environment.
- Live Ollama lifecycle tests were not run during this audit to avoid mutating local model/service state.
- Release bundle generation and Homebrew install smoke tests were not rerun during this audit because this change updates only `STATUS.md`.

## Known Issues, Risks, And Limitations

- The project is still on `0.3.5`; 1.0 materials are release-planning/draft references, not an active shipped 1.0 release line.
- Local Ollama operations are inherently stateful. Starting/stopping the service, warming models, downloading models, or deleting models can affect real user state.
- GUI validation is limited in headless/non-interactive environments; many UI paths rely on Kivy event-loop behaviour and manual spot checks.
- `run_tests.py full` can affect a real Ollama service and should be run only with explicit maintainer intent.
- Generated API docs under `docs/code/` may become stale when source changes unless regenerated deliberately.
- Homebrew distribution remains source-based and macOS/Apple-Silicon oriented.
- The saved-session v2 schema is the supported path; unsupported legacy sessions are intentionally rejected by schema helpers.

## Pending Tasks

### High Priority Before Release Freeze

- Repository-hygiene follow-ups from this audit have been addressed in this update (`sdf`, `config.yaml.bak`, stale alternate config paths, unused test-runner constant, stale roadmap wording, and stale standalone modelito diagram wording).

### Validation Pending

- Rerun `python -m pytest -q` in a supported Python environment with `requirements.txt` installed; the container default Python 3.14 environment lacks required dependencies.
- Optionally rerun `python validate_packaging_smoke.py` if release artefacts are expected to remain valid in the current environment.
- Rerun `python run_tests.py full` only in an environment where live Ollama start/stop is acceptable.
- Perform manual GUI smoke checks for `python run_batllm.py` and `python run_game_analyzer.py` before release tagging.

### Documentation Pending

- Keep `STATUS.md` current after every project-state change.
- Ensure `docs/README.md`, `docs/USER_GUIDE.md`, and `docs/CONTRIBUTING.md` stay aligned with UI labels, release workflow, and config defaults.
- Keep `docs/CHANGELOG.md` clear that 1.0 notes remain draft until an actual `v1.0.0` tag is prepared.
- Regenerate `docs/code/` only when API documentation updates are intentional.

## Next Steps

1. Run the narrow validation for this documentation update: `python -m pytest -q`.
2. Keep repository-hygiene checks active for future artefacts and generated-file drift.
3. Refresh stale documentation/diagram wording identified by the audit.
4. Run full non-live CI-equivalent checks across source, tests, packaging smoke, and Homebrew formula generation.
5. Schedule a maintainer-owned live Ollama validation pass before any release candidate.

## Longer-Term Steps

- Complete 1.0 local-desktop release hardening: UX consistency, first-run reliability, failure recovery, docs alignment, and platform bundle verification.
- Preserve deterministic replay and saved-session compatibility while improving gameplay and analyzer polish.
- Continue reducing Kivy-bound coupling in core game/session/replay logic to prepare for the planned 2.0 networked architecture.
- Design the 2.0 server contract before adding web or repository-backed prompt/game sharing.
- Add broader tests for malformed model responses, slow startup, missing models, session compatibility, analyzer edge cases, and packaged first-run behaviour.

Last updated: 2026-05-09 20:46
