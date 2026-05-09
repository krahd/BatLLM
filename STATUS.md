# BatLLM Status

Last updated: 2026-05-09 23:25

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

- `STATUS.md` previously used external SVG image links for diagrams. This update replaces that with inline SVG diagrams to match repository agent instructions.
- `src/configs/config-llama.yaml` still contains two stale `src/headers/system_instructions/...` paths for augmented modes. The shipped default `src/configs/config.yaml` points to existing `src/assets/system_instructions/...` files.
- `src/configs/config.yaml.bak` is tracked and appears to be a mutable configurator backup with a different model (`mistral-small:latest`) and altered gameplay values. It should be reviewed before release because backup/config artefacts are normally risky to keep in source control.
- A tracked top-level file named `sdf` appears to contain captured Ollama/model-pull terminal output with ANSI control sequences and model warm-up text. It is not referenced by the audited launchers, docs, or tests and should be reviewed for removal or archival.
- `run_tests.py` defines `OLLAMA_HELPER = ROOT / "src" / "ollama_service.py"`, but no such file exists and the constant is unused in the inspected runner.
- `docs/ROADMAP.md` still describes the "current 0.2.x line" even though `VERSION` is `0.3.5`; it should be refreshed in a future documentation pass.
- `docs/images/architecture-modelito.svg` still says "Modelito 1.2.2 Cleanup" in its title while the dependency is `modelito==1.4.0`; the inline diagram below uses current wording, but the standalone image should be updated or removed later.
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

### Inline Architecture Diagram

<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="720" viewBox="0 0 1120 720" role="img" aria-labelledby="batllm-arch-title batllm-arch-desc">
  <title id="batllm-arch-title">BatLLM architecture</title>
  <desc id="batllm-arch-desc">Architecture diagram showing launchers, Kivy surfaces, game logic, replay logic, configuration, the BatLLM LLM service facade, modelito, Ollama, packaging, tests, and documentation.</desc>
  <defs>
    <style>
      .bg { fill: #f7f5ef; }
      .box { fill: #fffdf8; stroke: #26323d; stroke-width: 2; }
      .accent { fill: #e9f2ff; stroke: #335c81; stroke-width: 2; }
      .state { fill: #fff2df; stroke: #8a5a14; stroke-width: 2; }
      .runtime { fill: #eef8ea; stroke: #44633f; stroke-width: 2; }
      .title { font: 700 26px 'Segoe UI', sans-serif; fill: #14202b; }
      .text { font: 500 14px 'Segoe UI', sans-serif; fill: #26323d; }
      .small { font: 500 12px 'Segoe UI', sans-serif; fill: #26323d; }
      .arrow { stroke: #26323d; stroke-width: 2.2; fill: none; marker-end: url(#arrow); }
    </style>
    <marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
      <path d="M0,0 L10,4 L0,8 z" fill="#26323d" />
    </marker>
  </defs>
  <rect class="bg" x="0" y="0" width="1120" height="720" />
  <text class="title" x="40" y="46">BatLLM Current Architecture</text>

  <rect class="box" x="40" y="90" width="220" height="110" rx="14" />
  <text class="text" x="62" y="124">Root launchers</text>
  <text class="small" x="62" y="150">run_batllm.py</text>
  <text class="small" x="62" y="172">run_game_analyzer.py</text>

  <rect class="box" x="330" y="70" width="250" height="145" rx="14" />
  <text class="text" x="352" y="104">Gameplay Kivy app</text>
  <text class="small" x="352" y="130">main.py, home/settings/history</text>
  <text class="small" x="352" y="152">game_board.py, bot.py, bullet.py</text>
  <text class="small" x="352" y="174">ollama_config_screen.py</text>

  <rect class="box" x="330" y="280" width="250" height="130" rx="14" />
  <text class="text" x="352" y="314">Standalone analyzer</text>
  <text class="small" x="352" y="340">analyzer_main.py</text>
  <text class="small" x="352" y="362">analyzer_model.py</text>
  <text class="small" x="352" y="384">load/review/board screens</text>

  <rect class="state" x="40" y="270" width="220" height="160" rx="14" />
  <text class="text" x="62" y="304">Config and state</text>
  <text class="small" x="62" y="330">config.yaml + app_config.py</text>
  <text class="small" x="62" y="352">BATLLM_HOME overlays</text>
  <text class="small" x="62" y="374">saved sessions</text>
  <text class="small" x="62" y="396">prompt/system assets</text>

  <rect class="accent" x="650" y="80" width="220" height="135" rx="14" />
  <text class="text" x="672" y="114">LLM service facade</text>
  <text class="small" x="672" y="140">src/llm/service.py</text>
  <text class="small" x="672" y="162">timeouts, readiness, metadata</text>
  <text class="small" x="672" y="184">start/stop/download/delete</text>

  <rect class="runtime" x="930" y="80" width="150" height="135" rx="14" />
  <text class="text" x="952" y="114">Runtime</text>
  <text class="small" x="952" y="140">modelito 1.4.0</text>
  <text class="small" x="952" y="162">local Ollama</text>
  <text class="small" x="952" y="184">models/server</text>

  <rect class="accent" x="650" y="285" width="220" height="125" rx="14" />
  <text class="text" x="672" y="319">Replay/session layer</text>
  <text class="small" x="672" y="345">history_manager.py</text>
  <text class="small" x="672" y="367">session_schema.py</text>
  <text class="small" x="672" y="389">replay_engine.py</text>

  <rect class="box" x="40" y="510" width="220" height="110" rx="14" />
  <text class="text" x="62" y="544">Docs and API reference</text>
  <text class="small" x="62" y="570">docs/*.md</text>
  <text class="small" x="62" y="592">docs/code generated output</text>

  <rect class="box" x="330" y="500" width="250" height="130" rx="14" />
  <text class="text" x="352" y="534">Tests and smoke tools</text>
  <text class="small" x="352" y="560">src/tests/*.py</text>
  <text class="small" x="352" y="582">ollama_mock_server.py</text>
  <text class="small" x="352" y="604">packaging_smoke.py</text>

  <rect class="box" x="650" y="500" width="220" height="130" rx="14" />
  <text class="text" x="672" y="534">Release packaging</text>
  <text class="small" x="672" y="560">release bundles</text>
  <text class="small" x="672" y="582">Homebrew formula</text>
  <text class="small" x="672" y="604">GitHub Actions</text>

  <path class="arrow" d="M260 145 H330" />
  <path class="arrow" d="M260 160 C295 160 295 345 330 345" />
  <path class="arrow" d="M580 148 H650" />
  <path class="arrow" d="M870 148 H930" />
  <path class="arrow" d="M455 215 V280" />
  <path class="arrow" d="M580 345 H650" />
  <path class="arrow" d="M760 285 V215" />
  <path class="arrow" d="M260 350 H330" />
  <path class="arrow" d="M760 410 V500" />
  <path class="arrow" d="M260 565 H330" />
  <path class="arrow" d="M580 565 H650" />
</svg>

### Inline Runtime Flow Diagram

<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="620" viewBox="0 0 1120 620" role="img" aria-labelledby="batllm-flow-title batllm-flow-desc">
  <title id="batllm-flow-title">BatLLM runtime flow</title>
  <desc id="batllm-flow-desc">Runtime flow from configuration and model selection through model readiness, prompt execution, turn resolution, persistence, and analyzer replay.</desc>
  <defs>
    <style>
      .bg { fill: #f6f7fb; }
      .box { fill: #ffffff; stroke: #324154; stroke-width: 2; }
      .decision { fill: #fff5dd; stroke: #8a6416; stroke-width: 2; }
      .accent { fill: #e9f1ff; stroke: #335c81; stroke-width: 2; }
      .runtime { fill: #edf7ee; stroke: #44633f; stroke-width: 2; }
      .title { font: 700 26px 'Segoe UI', sans-serif; fill: #15202b; }
      .text { font: 600 14px 'Segoe UI', sans-serif; fill: #27323b; }
      .small { font: 500 12px 'Segoe UI', sans-serif; fill: #27323b; }
      .arrow { stroke: #2f3a44; stroke-width: 2.2; fill: none; marker-end: url(#arrow2); }
    </style>
    <marker id="arrow2" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
      <path d="M0,0 L10,4 L0,8 z" fill="#2f3a44" />
    </marker>
  </defs>
  <rect class="bg" x="0" y="0" width="1120" height="620" />
  <text class="title" x="40" y="46">BatLLM Runtime Flow</text>

  <rect class="box" x="40" y="95" width="210" height="100" rx="14" />
  <text class="text" x="62" y="128">Load configuration</text>
  <text class="small" x="62" y="154">defaults + shipped YAML</text>
  <text class="small" x="62" y="176">optional BATLLM_HOME overlay</text>

  <rect class="box" x="310" y="95" width="210" height="100" rx="14" />
  <text class="text" x="332" y="128">Select model</text>
  <text class="small" x="332" y="154">Ollama screen or defaults</text>
  <text class="small" x="332" y="176">local or remote inventory</text>

  <polygon class="decision" points="620,80 725,145 620,210 515,145" />
  <text class="text" x="574" y="140">Local model</text>
  <text class="small" x="586" y="160">available?</text>

  <rect class="accent" x="790" y="70" width="250" height="120" rx="14" />
  <text class="text" x="812" y="104">Ensure model readiness</text>
  <text class="small" x="812" y="130">resolve timeout and warm-up</text>
  <text class="small" x="812" y="152">record last_served_model</text>
  <text class="small" x="812" y="174">report structured errors</text>

  <rect class="runtime" x="790" y="245" width="250" height="105" rx="14" />
  <text class="text" x="812" y="279">Download remote model</text>
  <text class="small" x="812" y="305">stream progress through modelito</text>
  <text class="small" x="812" y="327">refresh local inventory</text>

  <rect class="box" x="40" y="420" width="210" height="105" rx="14" />
  <text class="text" x="62" y="454">Submit player prompt</text>
  <text class="small" x="62" y="480">build command context</text>
  <text class="small" x="62" y="502">use independent/shared history</text>

  <rect class="accent" x="310" y="420" width="210" height="105" rx="14" />
  <text class="text" x="332" y="454">Model provider call</text>
  <text class="small" x="332" y="480">OllamaConnector to modelito</text>
  <text class="small" x="332" y="502">assistant response text</text>

  <rect class="box" x="580" y="420" width="210" height="105" rx="14" />
  <text class="text" x="602" y="454">Resolve turn</text>
  <text class="small" x="602" y="480">parse move/rotate/shoot/shield</text>
  <text class="small" x="602" y="502">update board and history</text>

  <rect class="box" x="850" y="420" width="210" height="105" rx="14" />
  <text class="text" x="872" y="454">Save or analyse</text>
  <text class="small" x="872" y="480">v2 session payload</text>
  <text class="small" x="872" y="502">replay in analyzer</text>

  <path class="arrow" d="M250 145 H310" />
  <path class="arrow" d="M520 145 H515" />
  <path class="arrow" d="M725 145 H790" />
  <path class="arrow" d="M620 210 V298 H790" />
  <path class="arrow" d="M915 350 V385 H145 V420" />
  <path class="arrow" d="M915 190 V385" />
  <path class="arrow" d="M250 472 H310" />
  <path class="arrow" d="M520 472 H580" />
  <path class="arrow" d="M790 472 H850" />
</svg>

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
- `docs/ROADMAP.md` describes 1.0 local desktop hardening and 2.0 networked-play direction, but its opening version wording needs a minor refresh from `0.2.x` to the current `0.3.x` line.
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
- `src/configs/config-llama.yaml` contains stale augmented-system-instruction paths under `src/headers/...` that do not match the current asset tree.
- Tracked `src/configs/config.yaml.bak` appears to be mutable local backup data and should be reviewed before any release freeze.
- Tracked `sdf` appears to be a captured Ollama terminal log and is likely accidental or at least unexplained repository material.
- `run_tests.py` has an unused `OLLAMA_HELPER` constant pointing to a missing `src/ollama_service.py` path.
- `docs/ROADMAP.md` has stale wording that describes the current line as `0.2.x`.
- Standalone diagram files under `docs/images/` still include modelito 1.2.2 wording even though current requirements pin modelito 1.4.0.
- Generated API docs under `docs/code/` may become stale when source changes unless regenerated deliberately.
- Homebrew distribution remains source-based and macOS/Apple-Silicon oriented.
- The saved-session v2 schema is the supported path; unsupported legacy sessions are intentionally rejected by schema helpers.

## Pending Tasks

### High Priority Before Release Freeze

- Decide whether to remove, ignore, or document the tracked `sdf` terminal-capture file.
- Decide whether tracked `src/configs/config.yaml.bak` is intentional; remove it or document why it is shipped.
- Fix stale `src/configs/config-llama.yaml` augmented-system-instruction paths.
- Remove or update the unused `OLLAMA_HELPER` constant in `run_tests.py`.
- Refresh `docs/ROADMAP.md` opening version wording from `0.2.x` to the current `0.3.x` line.
- Update or retire standalone `docs/images/*modelito.svg` files whose titles mention modelito 1.2.2.

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
2. Review and address the repository-hygiene findings (`sdf`, `config.yaml.bak`, stale alternate config paths, unused test-runner constant).
3. Refresh stale documentation/diagram wording identified by the audit.
4. Run full non-live CI-equivalent checks across source, tests, packaging smoke, and Homebrew formula generation.
5. Schedule a maintainer-owned live Ollama validation pass before any release candidate.

## Longer-Term Steps

- Complete 1.0 local-desktop release hardening: UX consistency, first-run reliability, failure recovery, docs alignment, and platform bundle verification.
- Preserve deterministic replay and saved-session compatibility while improving gameplay and analyzer polish.
- Continue reducing Kivy-bound coupling in core game/session/replay logic to prepare for the planned 2.0 networked architecture.
- Design the 2.0 server contract before adding web or repository-backed prompt/game sharing.
- Add broader tests for malformed model responses, slow startup, missing models, session compatibility, analyzer edge cases, and packaged first-run behaviour.

Last updated: 2026-05-09 23:25
