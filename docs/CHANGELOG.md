> ![BatLLM logo](./images/logo-small.png) **[Project](../README.md) · [Documentation](README.md) · [User Guide](USER_GUIDE.md) · [Contributing](CONTRIBUTING.md) · [Status](../STATUS.md) · [Releases](https://github.com/krahd/BatLLM/releases)**

# Changelog

## Unreleased

### Modelito 1.4.8 integration and main audit — 30 October 2026

- merged the published Modelito 1.4.8 consumer migration, restoring remote model-family discovery while preserving explicit endpoints, no-download startup and owned-service shutdown;
- verified merged main with all five hosted workflows, the full 310-test suite, real-model native gameplay/save/replay, research experiments and install-level Homebrew checks; and
- recorded four open findings in [the main audit](MAIN_AUDIT_2026_10_30.md): unsupported interpreter selection in bundle installers, unresponsive analyser file-row selection, small-window gameplay clipping and a download deadline overrun. These are findings, not repairs or release sign-off.

### Native audit repairs — 27 October 2026

- confirmed and repaired the three native-rehearsal findings: preview overflow, stale file-list refresh and false stopped status for an untagged model alias;
- contained long-filename overflow in the Recent Sessions footer found during native resize checks;
- added directory-refresh/selection and model-alias regressions, with native layout checks at three sizes; and
- preserved gameplay, prompting, inference, v2/v3 formats, defaults and version while retaining the unsigned release gates in [the audit follow-up](NATIVE_REHEARSAL_2026_10_27.md#verification-and-repair--27-october-2026).

### Native source rehearsal — 27 October 2026

- completed two native macOS games with real Ollama responses, session saving, in-app and standalone analysis, malformed-output handling and save-on-exit;
- independently replayed all 24 saved positions without a mismatch and ran all 293 automated tests with live smoke enabled; and
- recorded three open usability findings, selected evidence and unrun release gates in [the native rehearsal audit](NATIVE_REHEARSAL_2026_10_27.md).

### Post-merge audit repair — 26 October 2026

- routed the standalone editor through strict, deadline-aware inference and explicit-endpoint service operations; confirmed deletion, unload and download actions; made console cancellation local to its request/output;
- guarded every scheduled turn against game/round changes and rejected stale model-selection completions without unloading other clients’ models;
- separated temporary settings from persisted preferences and resolved context modes before constructing model input;
- aligned v3 structural checks with the committed JSON Schema, added strict imported-v2 rule validation and included the schema in runtime bundles;
- included the runtime import/resource closure in research packages and added isolated extracted generation/verification tests;
- removed implicit model pulls from daemon startup and added explicit model-name download recovery while automatic Modelito catalogue discovery remains unsupported; and
- recorded per-finding repair disposition and validation in [the post-merge audit](ADVERSARIAL_AUDIT_2026_10_26.md).

### Adversarial audit repair — 25 October 2026

- upgraded runtime and Homebrew pins to Modelito 1.4.6 and shared strict, deadline-aware native inference between gameplay and research;
- added wire-level payload, timeout, unavailable-server and malformed-response regressions; corrected streaming defaults in the CI mock;
- removed independent Modelito configuration discovery from service operations and required endpoint/PID/birth-time ownership before shutdown;
- restored conversation histories on round cancellation and added v2 action validation, grounding checks and turn-continuity warnings;
- deferred model persistence until readiness succeeds, rejected non-finite timeout input and non-mapping YAML sections, escaped analyser content, and removed rendering mutations;
- moved default saved sessions into the user data directory, copying legacy JSON files without overwriting originals or user files;
- moved startup inspection off the UI thread, removed live metadata I/O from saving, bounded management subprocesses and opened the official download page instead of executing remote installer scripts;
- separated platform runtime bundles from source/research archives and pinned all workflow actions to commits; and
- recorded upstream Modelito lifecycle/deadline limitations and native validation gates in [the audit verification](ADVERSARIAL_AUDIT_2026_10_25.md).

### Reliability and session integrity

- incorporated AlanJoskowicz’s PR #60 model-selection fix, preserving contributor commits;
- restored the `smollm2` first-install default and separated saved configuration from versioned defaults across installation channels;
- preserved existing overlays and legacy checkout preferences, guarded shipped defaults, used the atomic writer for last-served-model persistence, and moved the standalone editor to user preferences;

- extracted canonical local model names from Ollama CLI rows before selection, saving, and warm-up, and avoided modelito's unparsed-row availability check;
- preserved model-selection error messages for deferred UI alerts, preventing a secondary `NameError`;
- isolated model conversation histories across manual and normal game restarts;
- guarded asynchronous game lifecycle callbacks against retired games and turns;
- exported only completed analyzer-valid turns from saved sessions;
- strengthened nested session and replay-state validation, including bot identity consistency;
- preserved rejected prompts and surfaced save failures without discarding user input; and
- isolated tests from repository and user configuration through a temporary `BATLLM_HOME`.

### Research artefact

- added the schema-v3 headless research runtime and verifier;
- added differential semantics, perturbation, serialization, and overhead experiments;
- committed the implementation-owned URUCON reproducibility artefact; and
- moved editable manuscript ownership to `krahd/academic-writing` while retaining software evidence here.

### Dependencies and tooling

- excluded virtual environments and generated files from documentation link scans, fixing Windows CI failures caused by third-party package documentation;
- repaired the job-level CI interpreter expression to use the available matrix context so the Python/platform test matrix can start;

- aligned the runtime on `modelito==1.4.5`, `ollama>=0.6.2`, `psutil==7.2.2`, `PyYAML==6.0.3`, and `requests>=2.34.2`;
- restored the Python `3.10`–`3.12` multiplatform non-live CI matrix and maintained Pylint gate;
- added focused dependency, packaging, mock-Ollama, and research workflows; and
- retained repository version `0.3.6` while 1.0 release criteria remain unsigned.

### Documentation and housekeeping

- added a root project README and converted `docs/README.md` into a documentation index;
- rewrote the User Guide, contributor guide, status report, release criteria, state reference, and maintainer checklists around current behaviour;
- added automated documentation validation;
- corrected stale release-bundle state, workflow, test-command, and URUCON CI descriptions; and
- removed obsolete audit patches, overlay archives, duplicated implementation payloads, one-off PR helper files, and historical documentation-change reports.

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
