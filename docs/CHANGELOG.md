> ![BatLLM logo](./images/logo-small.png) **[Overview](DOCUMENTATION.md) · [Readme](README.md) · [User Guide](USER_GUIDE.md) · [Contributing](CONTRIBUTING.md) · [FAQ](FAQ.md) · [Changelog](CHANGELOG.md) · [Credits](CREDITS.md) · [Code Docs](code/html/index.html)**

# Changelog

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
