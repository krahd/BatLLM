> ![BatLLM logo](./images/logo-small.png) **[README](README.md) · [User Guide](USER_GUIDE.md) · [Contributing](CONTRIBUTING.md) · [FAQ](FAQ.md) · [Changelog](CHANGELOG.md) · [Credits](CREDITS.md) · [Releases](https://github.com/krahd/BatLLM/releases)**

# Changelog

## Unreleased

- keeping release line on `0.x` pending maintainer validation; repository `VERSION` is now `0.3.5`
- continue release hardening and checklist execution before any `1.0.0` tag decision

## Draft v1.0.0 Release Notes (not released)

### Modelito 1.4.0 Integration

- upgraded `modelito` dependency from `1.2.2` to `1.4.0`
- implemented `ensure_model_ready_detailed()` for structured `ReadinessResult` objects instead of boolean polling
- added configurable `warmup_timeout` parameter to `start_service()` orchestration (default 30.0s)
- imported transport error handling types (`ErrorEnvelope`, `ResponseEnvelope`, `TransportPolicy`) from `modelito` for improved error normalization
- updated Ollama config screen to use the new readiness result object for richer UI lifecycle feedback (phase, elapsed time, source details, error information)
- updated service layer to pass `warmup_timeout` through to modelito's `start_service()` call
- added a user-editable warmup-timeout control to the Ollama screen and CLI support for `python -m llm.service start --warmup-timeout ...`
- added focused tests for detailed readiness success/failure handling and warmup-timeout config persistence
- added saved `llm_metadata` snapshots to exported sessions and exposed that metadata in a new Game Analyzer inspector tab

### 1.0 Release Hardening

- fixed `run_tests.py` path bootstrap so full mode works from repository root without ad-hoc environment setup
- added unified packaging smoke validation with installer and Homebrew install-level smoke modes
- tightened service stop behaviour so force-kill escalation only targets processes already terminated by BatLLM
- regenerated API docs and aligned Doxygen metadata to the repository release version
- verified full-suite test execution including live-Ollama gated smoke path

### Modelito 1.2.2 Direct Integration

- pinned BatLLM to `modelito==1.2.2`
- moved gameplay requests to direct `modelito` usage in `src/game/ollama_connector.py`
- switched the Ollama screen, configurator console, smoke helpers, and test CLI to direct `modelito` service and provider helpers
- removed the remaining pre-release compatibility and stale backup files that kept obsolete non-gameplay HTTP paths alive
- updated the maintained docs and status report to describe the direct `modelito 1.2.2` architecture consistently

## v0.3.3 - 2026-04-21

### Modelito migration

- migrated generic Ollama lifecycle and helper functions to the published `modelito` package and routed the then-current compatibility wrapper through `modelito.ollama_service`
- removed legacy migration documentation (`docs/MIGRATION_TO_MODELITO.md`)
- bumped repository `VERSION` to 0.3.3

## v0.3.2 - 2026-04-06

### Homebrew Tap Automation

- added a dedicated GitHub Actions workflow that publishes `batllm.rb` to `krahd/homebrew-tap` for pushed release tags and manual dispatches
- made the tap publish path reuse `create_homebrew_formula.py` and the shared rebase-and-retry push flow so first-time formula creation and concurrent tap updates are handled consistently

### Maintainer Documentation

- documented the automatic shared-tap publish path and the required `HOMEBREW_TAP_TOKEN` secret in the Homebrew maintainer docs
- updated the contributor guide's release workflow notes to mention the source-based Apple Silicon tap publishing automation

## v0.3.1 - 2026-04-06

### Homebrew Distribution

- added Homebrew distribution support with `create_homebrew_formula.py`, pinned packaging requirements, and regression coverage for the formula and packaged runtime overlay
- added `BATLLM_HOME`-aware packaged-install behavior so writable config and saved-session data stay outside the read-only Homebrew cellar

### Installation Documentation

- added end-user Homebrew install and launch instructions for Apple Silicon macOS across the maintained docs
- documented the Homebrew maintainer workflow separately from the end-user install path in the repository documentation

## v0.3.0 - 2026-04-05

### Fresh Install Defaults

- changed the primary shipped Ollama model from `qwen3:30b` to `smollm2` so first-run BatLLM is more likely to work on modest local hardware
- stopped shipping a pre-populated `llm.last_served_model`, so a new installation starts with a clean first-run model state and only records the served model after a successful warm-up
- aligned the built-in local timeout table with the new default by adding a shared `smollm2` timeout profile

### Validation And Documentation

- added fresh-install startup tests that verify BatLLM falls back to the configured default model when no served-model history exists
- strengthened shipped-config validation to pin the expected first-install Ollama defaults in the repository test suite
- updated the contributor guide's documented sample config to match the shipped first-install defaults

## v0.2.5 - 2026-04-05

### Timeout Configuration and Recovery

- centralised model-aware Ollama timeout resolution across gameplay requests, service warm-up, and live smoke helpers
- added built-in timeout defaults for common local models while keeping explicit per-model and global timeout overrides
- hardened timeout message formatting and fixed the remaining timeout/configuration edge cases that could surface during live play

### Ollama Config Screen

- added per-model timeout controls to `Local Models`, including the effective-timeout display, explicit override save, and reset-to-default action
- removed saved timeout overrides automatically when a local model is deleted

### Prompt Dialog Esc Handling

- made the prompt-load dialog own `Esc` while it is open so it dismisses the dialog instead of falling through to the home-screen exit confirmation
- added regression coverage for both the dialog-owned `Esc` flow and the model-timeout precedence path

## v0.2.4 - 2026-04-05

### Prompt and Keyboard UX

- made the prompt-load dialog support immediate keyboard navigation with `Up`, `Down`, and `Enter`, and made `Esc` follow the same path as `Cancel`
- initialised the first visible prompt automatically when the dialog opens so keyboard-only prompt loading works without a prior mouse click

### Ollama Timeout Recovery

- raised the default Ollama request-timeout fallback from 55 seconds to 120 seconds for large local models
- retried timed-out Ollama chat requests once before surfacing a structured timeout error to the game board
- added round-level timeout recovery with `ERR` versus `Cancel Round` choices and a per-round "remember this choice" option
- preserved cancelled rounds in session history and rolled live gameplay state back to the round-start snapshot when a timeout cancels the round

### Live Ollama Tooling and Tests

- aligned the live smoke test and Ollama warmup helper with the same large-model timeout expectations as the runtime connector
- added regression coverage for prompt-dialog keyboard handling, timeout helper logic, startup timeout resolution, and round-timeout recovery

## v0.2.3 - 2026-04-05

### Game Analyzer

- added a new read-only `Game Analyzer` mode, available both from the home screen and through `run_game_analyzer.py`
- added analyzer-compatible v2 session exports with `schema_version`, `session_type`, `saved_at`, and per-round `gameplay_settings_snapshot`
- added a shared Kivy-free replay engine so saved sessions are replayed against the original round rules instead of the current config
- added analyzer navigation for multi-game sessions, per-round replay, prompts, plays, state diffs, round settings, and replay insights
- added platform release-bundle launchers for the standalone analyzer

### Ollama Lifecycle UX

- added startup prompts to install Ollama when the CLI is missing
- added startup prompts and settings-backed auto-start behaviour for Ollama when it is installed but not running
- added automatic Ollama shutdown on app exit when `Stop Ollama Automatically on BatLLM Quit` is enabled
- added `Install Ollama` to the Ollama control screen with install vs reinstall confirmation
- persisted `llm.last_served_model` so BatLLM can warm the same model when it starts Ollama again
- made Ollama shutdown more resilient on macOS when process socket inspection is permission-limited

### Input and Navigation

- made `Esc` on the Game Analyzer load and review screens behave like the `Back` button
- made `Esc` on the save-session confirmation behave like pressing `No`

### Documentation

- updated the README, user guide, and contributor guide to reflect the install flow, startup prompts, new settings, and `last_served_model`
- replaced the user-only FAQ with a shared user/developer FAQ focused on recurring non-trivial questions
- aligned the overview docs and docs index with the new FAQ scope
- removed `DOCUMENTATION.md` and kept `README.md` as the sole overview and documentation entry point
- removed outdated interface illustration references from the README while keeping the animated gameplay demo
- added a compact compatibility matrix, glossary, and release-bundle troubleshooting appendix to the README
- added a lightweight documentation review checklist to the PR workflow in the contributor guide
- reordered the shared documentation navigation so `README` is the first item and removed the obsolete SVG interface diagrams from the repository
- added a dedicated roadmap document and linked it from the contributor guide

## v0.2.1 - 2026-04-03

### Packaging Fixes

- replaced the non-installable `kivymd==2.0.1.dev0` requirement with the stable PyPI release `kivymd==1.2.0`
- aligned fresh-install behaviour with the dependency set used in multiplatform CI and release bundles

## v0.2.0 - 2026-04-03

### Cross-Platform Support

- added `run_batllm.py` as the repository-root launcher for macOS, Linux, and Windows
- added `src/ollama_service.py` as a cross-platform Ollama lifecycle helper
- moved the Ollama screen away from a Unix-only shell-script dependency
- made resource, prompt, system-instruction, and save-session paths resolve from the repository instead of the current working directory
- added `run_tests.py` as the cross-platform test runner and kept `run_tests.sh` as a Unix wrapper
- added a GitHub Actions matrix to validate the non-live suite on Ubuntu, Windows, and macOS

### Release Tooling

- added a repository `VERSION` file
- added `create_release_bundles.py` to generate source, Windows, macOS, and Linux release archives
- documented the new tagged-release workflow and platform-specific launchers

## v0.1.0 - 2026-04-03

### Documentation

- replaced the placeholder main documentation page with a current project overview
- rewrote the README, user guide, contributor guide, and FAQ to match the current codebase
- added an actual documentation landing page in `docs/index.html`
- added Ollama workflow diagrams for the control screen and model pickers
- aligned the docs with the current UI labels, including the `Ollama Config` button
- normalised the maintained documentation set to British English
- consolidated the developer-facing configuration, testing, and troubleshooting material into `CONTRIBUTING.md`
- rewrote `USER_GUIDE.md` as a game manual and restored the screen recording
- rewrote `CONTRIBUTING.md` as a standard developer and contribution manual
- removed the obsolete standalone `CONFIGURATION.md`, `TESTING.md`, and `TROUBLESHOOTING.md` pages
- added `DOCUMENTATION_CHANGE_REPORT.md` to summarise the documentation restructure

### Ollama UX

- documented the modal model pickers, including `Esc` dismissal and outside-click dismissal
- documented the difference between local model selection and remote model download
- documented that BatLLM may stop the previously managed model before warming a newly selected one

### Repository Consistency

- added the missing dependencies required by the then-current Ollama integration to `requirements.txt`
- removed the stray space-prefixed `primary_color` key from config defaults and sample configs
