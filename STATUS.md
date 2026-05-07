# BatLLM Status

Last updated: 2026-05-07 00:04

## Current State

BatLLM is currently at repository version `0.3.3` and remains centered on two maintained Python/Kivy surfaces:

- the main BatLLM gameplay application
- the read-only Game Analyzer for replay and review workflows

The repository now routes maintained Ollama lifecycle/model-management behavior through `modelito 1.4.0`, with high-priority features for structured model readiness results and configurable service warmup timeout.

## Current Focus

- Upgraded BatLLM to `modelito 1.4.0` with high-priority feature integration.
- Implemented `ensure_model_ready_detailed()` for structured lifecycle feedback.
- Added configurable `warmup_timeout` support through config, service CLI, and the Ollama screen.
- Added saved-session `llm_metadata` snapshots and exposed them in the Game Analyzer UI.
- Keep the maintained docs, broader validation notes, and packaging-sensitive checks aligned with the enhanced `modelito 1.4.0` architecture.

## Architecture Notes

- Launchers: `run_batllm.py`, `run_game_analyzer.py`
- Main app entrypoint: `src/main.py`
- Gameplay and LLM request orchestration: `src/game/`, `src/llm/`
- Ollama/runtime service surface: `src/llm/service.py`
- UI/runtime model management: `src/view/ollama_config_screen.py`
- Config tooling: `src/configs/configurator.py`
- Tests: `src/tests/`

## Architecture Diagram

![BatLLM architecture](docs/images/architecture-modelito.svg)

## Runtime Flow Diagram

![BatLLM runtime flow](docs/images/request-flow-modelito.svg)

## Recent Changes In This Work Session

- Upgraded `modelito` dependency from `1.2.2` to `1.4.0` in `requirements.txt`.
- Implemented high-priority features from modelito 1.4.0:
  - **Structured readiness results**: Migrated from `ensure_model_ready()` (boolean) to `ensure_model_ready_detailed()` returning `ReadinessResult` with `success`, `phase`, `message`, `source`, `elapsed_seconds`, and `error` fields.
  - **Configurable warmup timeout**: Added `warmup_timeout` parameter (default 30.0s) to `start_service()` call to allow customization of server startup timeout.
  - **Error envelope support**: Imported `ErrorEnvelope`, `ResponseEnvelope`, `TransportPolicy` from modelito for improved error normalization.
- Updated `src/view/ollama_config_screen.py`:
  - Changed `_ensure_model_serving_via_modelito()` and `_ensure_model_serving()` to use `ensure_model_ready_detailed()`.
  - Enriched lifecycle logging with `elapsed_seconds`, `phase`, and `source` information from the result object.
  - Simplified error handling by checking `result.success` and accessing structured error/message fields.
- Updated `src/llm/service.py`:
  - Modified `start_service()` signature to accept `warmup_timeout: float = 30.0` parameter.
  - Added error envelope imports for future error handling improvements.
  - Passed `warmup_timeout` through to modelito's `start_service()` call.
- Added `llm.warmup_timeout` to the shipped config/default config flow and wired it into the Ollama screen plus the `python -m llm.service start --warmup-timeout ...` CLI path.
- Added saved `llm_metadata` snapshots to session export and exposed that metadata in the analyzer's new `Model` inspector tab.
- Updated the maintained docs (`docs/README.md`, `docs/USER_GUIDE.md`, `docs/CONTRIBUTING.md`, `docs/CHANGELOG.md`) for modelito 1.4.0, warmup-timeout controls, and analyzer metadata.
- Fixed broader pytest collection for `src/tests/test_homebrew_packaging.py` by moving the repo-root `sys.path` setup ahead of repo-root helper imports.
- Updated the legacy `src/tests/test_ollama_config_screen.py` start/stop assertion to match the new `--warmup-timeout` service invocation.
- Added explicit `requests==2.32.4` pin to the root runtime requirements so the repository manifest remains a superset of the Homebrew runtime subset.

## Validation

Completed in this work session:

- Upgraded the active virtual environment from `modelito 1.2.2` to `modelito 1.4.0`.
- Updated `requirements.txt` to pin `modelito==1.4.0`.
- Updated `src/llm/service.py` with `warmup_timeout` support and modelito transport-envelope imports.
- Updated both readiness paths in `src/view/ollama_config_screen.py` to use `ensure_model_ready_detailed()` and structured readiness results.
- `./.venv_BatLLM/bin/python -m py_compile src/llm/service.py src/view/ollama_config_screen.py src/game/session_schema.py src/game/history_manager.py src/analyzer_model.py src/view/analyzer_review_screen.py src/tests/test_ollama_config_screen_logic.py src/tests/test_multiplatform_support.py src/tests/test_game_analyzer.py` -> passed.
- `./.venv_BatLLM/bin/python -m pytest -q src/tests/test_ollama_config_screen_logic.py src/tests/test_multiplatform_support.py src/tests/test_game_analyzer.py` -> 57 passed.
- `./.venv_BatLLM/bin/python -m pytest -q src/tests/test_homebrew_packaging.py` -> 7 passed.
- `./.venv_BatLLM/bin/python -m pytest -q` -> 138 passed, 2 skipped.

Not yet completed in this work session:

- Doxygen/code-doc regeneration for `docs/code/`

## Known Risks And Gaps

- `src/llm/service.py` still owns BatLLM-specific config overlay and timeout policy; that module should stay narrow and should not grow back into a generic Ollama abstraction layer.
- Kivy/UI behavior around model-management flows needs regression coverage whenever service helpers or model lifecycle logic changes.
- Packaging-sensitive test coverage is clean, but an actual release-bundle or Homebrew build/install smoke run was not executed in this work session.
- Generated `docs/code/` output still reflects older code snapshots until Doxygen is rerun.

## Next Prioritized Steps

1. Run an actual release-bundle or Homebrew build/install smoke validation if this work is headed toward a publish step.
2. Regenerate `docs/code/` if the generated API docs are expected to ship with this refactor.
3. Evaluate whether `src/llm/service.py` startup orchestration should further collapse to direct `modelito.start_service/stop_service` calls in all code paths.

## Longer-term Steps and Decisions

1. GUI: webapp surface? Yes/no? If Yes: in addition to or instead of Kivy?
2. LAN multiplayer
3. Internet multiplayer
4. Library / repo / examples of prompts
5. Computer-controlled player (flavours: prompted, AI-directly, programatically)

---

Last updated: 2026-05-07 00:04
