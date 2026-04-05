> ![BatLLM logo](./images/logo-small.png) **[README](README.md) · [User Guide](USER_GUIDE.md) · [Contributing](CONTRIBUTING.md) · [FAQ](FAQ.md) · [Changelog](CHANGELOG.md) · [Credits](CREDITS.md) · [Releases](https://github.com/krahd/BatLLM/releases)**

# Changelog

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

- added the missing `requests` and Python `ollama` dependencies to `requirements.txt`
- removed the stray space-prefixed `primary_color` key from config defaults and sample configs
