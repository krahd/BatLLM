# BatLLM Status

Last updated: 2026-05-10 00:51

## Project Purpose

BatLLM is a Python/Kivy research, education, and game project for exploring AI-mediated play, prompt quality, LLM behaviour, and local-model workflows. The repository currently contains a playable local desktop game, a standalone read-only Game Analyzer, local Ollama lifecycle and model-management helpers routed through `modelito`, release-bundle tooling, Homebrew formula generation, generated API reference artefacts, and maintained user/developer documentation.

The project should remain practical, critical, and educational. Destructive or expensive local-model actions must stay explicit because BatLLM can start and stop a real Ollama service, download or delete models, and save user-created sessions.

## Setup And Run Instructions

### Supported Runtime

- Python: `>=3.10` and `<3.13` enforced by the launcher compatibility helper.
- Main UI framework: Kivy `2.3.1` plus KivyMD `1.2.0`.
- LLM/runtime integration: Ollama through `modelito==1.4.0` and `ollama==0.5.3`.
- Default shipped model: `smollm2` with first-run `last_served_model` intentionally blank.
- Repository version: `0.3.6`.

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

- Tracked files: 610.
- Tracked source/test/application files under `src/`: 81.
- Tracked documentation files and generated API artefacts under `docs/`: 505.
- Test files: 14 tracked smoke/test files with 157 collected test functions by static scan.
- Key top-level launchers and tooling: `run_batllm.py`, `run_game_analyzer.py`, `run_tests.py`, `create_release_bundles.py`, `create_homebrew_formula.py`, `validate_packaging_smoke.py`, `start_ollama.sh`, `stop_ollama.sh`, `scripts/cmr-r`, and `tools/ollama_mock_server.py`.
- CI workflows present: `.github/workflows/multiplatform.yml` and `.github/workflows/publish-homebrew-tap.yml`.
- Packaging subtree present: `packaging/homebrew/README.md` and `packaging/homebrew/requirements.txt`.

### Notable Audit Findings

- Root launchers and `run_tests.py` now insert `src/` into `sys.path` before importing local modules, so the documented root commands no longer depend on an already-exported `PYTHONPATH`.
- `src/util/compat.py` now enforces the documented supported Python window `>=3.10,<3.13`.
- `src/configs/config-llama.yaml` and `src/configs/config-phi.yaml` were refreshed to use current schema keys, matching system-instruction asset paths, warmup-timeout defaults, and model names that match the file intent.
- Maintained docs were aligned with repository version `0.3.6`, supported Python `>=3.10,<3.13`, and the shipped `llm.warmup_timeout` default.
- Repository patch version was bumped from `0.3.5` to `0.3.6`.
- Mock-Ollama smoke validation now accepts a responding `/api/version` endpoint when process-level inspection cannot identify the mock server as an Ollama process.
- Generated Doxygen output under `docs/code/` was regenerated after source and version changes. Existing Doxygen warnings are mostly undocumented Kivy/test helper classes and remain non-blocking documentation debt.
- Architecture and runtime-flow SVG diagrams were redrawn with larger canvases, wrapped text, boundary-aligned connectors, plain arrow labels, and clearer label placement.
- `docs/index.html` is now the public GitHub Pages showcase site for `https://krahd.github.io/BatLLM/`; GitHub Pages now serves from branch `main` and path `/docs`, the hero no longer uses a diagram background or top-of-page gameplay image, the page uses a darker modernised visual system, grant/provenance notes are surfaced in a dedicated section, Tomas Laurenzo attribution remains in provenance/footer copy, the demo GIF is used once in-page, and inline text links are no longer bolded.
- The git worktree was clean at the start of this audit; current changes are intentional audit/remediation updates.

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
- `VERSION`: active repository version (`0.3.6`).
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
- `docs/index.html` is the static project showcase served by GitHub Pages from branch `main` and path `/docs`.
- `docs/.nojekyll` keeps GitHub Pages from applying Jekyll processing to the static documentation tree.
- `docs/FIRST_RUN_RELEASE_CHECKLIST.md` and `docs/UI_UNIFICATION_PLAN_1_0.md` remain release-preparation references.
- `docs/images/architecture-modelito.svg` and `docs/images/request-flow-modelito.svg` are maintained standalone SVG diagrams used by `STATUS.md`; they were refreshed for legibility and connector accuracy.
- `docs/code/` contains generated Doxygen HTML/LaTeX output and should be treated as generated documentation.

## Tests And Verification Status

### Latest Commands Run For This Audit

- `git status --short` -> passed; confirmed the worktree was clean before edits.
- Repository audit commands using `rg`, `git ls-files`, `find`, `sed`, and `wc` -> passed; checked tracked inventory, maintained docs, source modules, config files, TODO markers, stale version/path references, ignored local artefacts, generated docs, and test inventory.
- `.venv_BatLLM/bin/python -m pytest -q src/tests/test_multiplatform_support.py src/tests/test_history_compact.py` -> `38 passed`.
- `.venv_BatLLM/bin/python -m pytest -q` -> `155 passed, 2 skipped`; rerun after the `0.3.6` version bump.
- `.venv_BatLLM/bin/python run_tests.py core` -> `4 passed`.
- `.venv_BatLLM/bin/python -m compileall -q src run_batllm.py run_game_analyzer.py run_tests.py create_release_bundles.py create_homebrew_formula.py validate_packaging_smoke.py` -> passed.
- `.venv_BatLLM/bin/python validate_packaging_smoke.py` -> initially failed inside the restricted sandbox because PyPI DNS was blocked; rerun with network permission and passed (`Packaging smoke validation passed.`).
- CI-style mock Ollama smoke: started `tools/ollama_mock_server.py` on `127.0.0.1:11434`, then ran `BATLLM_RUN_OLLAMA_SMOKE=1 PYTHONPATH=src KIVY_HOME=/tmp/batllm-kivy-smoke KIVY_NO_ARGS=1 KIVY_NO_CONSOLELOG=1 .venv_BatLLM/bin/python -m pytest -q src/tests/smoke_llm_payload.py` with local socket permission -> `2 passed`; the mock server was stopped afterwards.
- `rg -n "0\.3\.5" VERSION docs src ...` -> passed with no matches after the `0.3.6` version bump.
- `doxygen docs/code/dox_config.properties` -> passed; regenerated tracked API docs with `PROJECT_NUMBER = 0.3.6` and reported existing undocumented-class/member warnings.
- Documentation local-link sanity check for `docs/*.md` -> passed (`documentation-local-links-ok`).
- `python3 - <<'PY' ...` XML parse check for `docs/images/architecture-modelito.svg` and `docs/images/request-flow-modelito.svg` -> passed.
- `rsvg-convert -o /tmp/architecture-modelito.png docs/images/architecture-modelito.svg` and `rsvg-convert -o /tmp/request-flow-modelito.png docs/images/request-flow-modelito.svg` -> passed; both diagrams rendered to temporary PNGs without errors.
- GitHub Pages configuration check with `gh api repos/krahd/BatLLM/pages` -> passed; Pages serves `https://krahd.github.io/BatLLM/` from branch `main` and path `/docs`.
- `python3 - <<'PY' ...` static HTML reference check for `docs/index.html` -> passed; verified local asset/doc references and visible grant-support copy.
- Local static server check with `python3 -m http.server 8040` from `docs/` plus `curl` -> passed; confirmed `index.html`, `images/logo-small.png`, `images/request-flow-modelito.svg`, and `images/architecture-modelito.svg` were served successfully.
- Pages build request with `gh api repos/krahd/BatLLM/pages/builds --method POST` -> passed; build `991944945` completed successfully for commit `7fa9168`.
- Published-site verification with `curl -sL https://krahd.github.io/BatLLM/` -> passed; confirmed the public HTML includes `Grant-supported research software`, `2024 Arts & Humanities Grant Program`, and `CHA Small Grant`.
- Published asset checks with `curl -I` for `/images/logo-small.png`, `/images/request-flow-modelito.svg`, and `/images/architecture-modelito.svg` -> passed with HTTP 200 responses.

### Recent Previously Recorded Validation

The previous status report recorded these successful checks from the same release-hardening period. They remain useful historical evidence but were not rerun unless listed above.

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
- A headless launcher import attempt reached Kivy window initialisation and failed with `Unable to get a Window`; this is an environment limitation, not a substitute for manual GUI launch validation.
- `python run_tests.py full` was not run during this audit because it can start and stop a real local Ollama service.
- Homebrew install-level smoke (`validate_packaging_smoke.py --run-homebrew-install-smoke`) was not run because it installs/uninstalls through the local Homebrew installation.
- Quick Look HTML thumbnail rendering with `qlmanage` was not completed because the sandbox rejected Quick Look initialisation; local HTTP/static checks were used instead.

## Known Issues, Risks, And Limitations

- The project is still on `0.3.6`; 1.0 materials are release-planning/draft references, not an active shipped 1.0 release line.
- Local Ollama operations are inherently stateful. Starting/stopping the service, warming models, downloading models, or deleting models can affect real user state.
- GUI validation is limited in headless/non-interactive environments; many UI paths rely on Kivy event-loop behaviour and manual spot checks.
- `run_tests.py full` can affect a real Ollama service and should be run only with explicit maintainer intent.
- Generated API docs under `docs/code/` are current for this audit but remain large and noisy because Doxygen also tracks LaTeX PDF artefacts.
- Homebrew distribution remains source-based and macOS/Apple-Silicon oriented.
- The saved-session v2 schema is the supported path; unsupported legacy sessions are intentionally rejected by schema helpers.

## Pending Tasks

### High Priority Before Release Freeze

- No new high-priority code or maintained-documentation remediation from this audit remains open.

### Validation Pending

- Perform manual GUI smoke checks for `python run_batllm.py` and `python run_game_analyzer.py` before release tagging.
- Rerun `python run_tests.py full` only when the maintainer is ready for BatLLM to start/stop the configured real local Ollama service.
- Run Homebrew install-level smoke only when mutating the local Homebrew installation is acceptable.
- Complete Linux and Windows manual first-run checklist execution on native hosts before a release candidate.

### Documentation Pending

- Keep `STATUS.md` current after every project-state change.
- Ensure `docs/README.md`, `docs/USER_GUIDE.md`, and `docs/CONTRIBUTING.md` stay aligned with UI labels, release workflow, and config defaults.
- Keep `docs/CHANGELOG.md` clear that 1.0 notes remain draft until an actual `v1.0.0` tag is prepared.
- Regenerate `docs/code/` only when API documentation updates are intentional, and review generated PDF churn before committing.

## Next Steps

1. Run maintainer-owned manual GUI smoke checks on a machine with a display.
2. Run maintainer-owned live Ollama validation before any release candidate if local Ollama state can be safely mutated.
3. Complete the Linux and Windows first-run checklist on native hosts.
4. Keep repository-hygiene checks active for future artefacts and generated-file drift.
5. Keep `STATUS.md`, release notes, and generated API docs aligned with future source/config changes.

## Longer-Term Steps

- Complete 1.0 local-desktop release hardening: UX consistency, first-run reliability, failure recovery, docs alignment, and platform bundle verification.
- Preserve deterministic replay and saved-session compatibility while improving gameplay and analyzer polish.
- Continue reducing Kivy-bound coupling in core game/session/replay logic to prepare for the planned 2.0 networked architecture.
- Design the 2.0 server contract before adding web or repository-backed prompt/game sharing.
- Add broader tests for malformed model responses, slow startup, missing models, session compatibility, analyzer edge cases, and packaged first-run behaviour.

Last updated: 2026-05-10 00:51
