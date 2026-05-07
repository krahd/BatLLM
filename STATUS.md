# BatLLM Status

Last updated: 2026-05-07 17:13

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

## Known Issues, Risks, And Limitations

- `src/llm/service.py` still owns BatLLM-specific overlay logic and timeout policy; avoid re-expanding it into a generic provider abstraction already handled by `modelito`.
- Packaging helpers and the unified smoke validator execute successfully, but an end-to-end install smoke run of the generated release bundle or Homebrew formula was not executed in this session.
- Generated API docs in `docs/code/` have not been regenerated in this session.

## Recurring Tasks

- Keep hygiene checks current as packaging and release scripts evolve.

## Pending Tasks

- Run an end-to-end install smoke validation using the generated release bundle or generated Homebrew formula before a publish step.
- Regenerate `docs/code/` if generated API docs are intended to ship with this update.
- Continue narrowing `src/llm/service.py` where direct `modelito` calls can replace local orchestration branches without changing BatLLM-specific behaviour.

## Next Steps

1. Run end-to-end install smoke validation for either generated release bundles or a local Homebrew formula install before publish.
2. Regenerate and review generated docs under `docs/code/` if required for release artefacts.
3. Keep STATUS and maintained docs aligned with any additional runtime or packaging changes.

## Longer-Term Steps

1. Decide GUI direction for web-app surface versus Kivy-only roadmap.
2. LAN multiplayer support.
3. Internet multiplayer support.
4. Prompt library/repository and examples.
5. Additional computer-controlled player modes.

---

Last updated: 2026-05-07 17:13
