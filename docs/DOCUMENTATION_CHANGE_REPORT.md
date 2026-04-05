# Documentation Change Report

## 2026-04-04 FAQ Consolidation And Documentation Cleanup

### Scope

This revision tightened the FAQ, aligned the rest of the maintained documentation around that new scope, and removed outdated README interface illustrations that no longer matched the actual UI.

### FAQ Changes

- replaced the previous user-only FAQ with a mixed user/developer FAQ
- removed trivial screen-mechanics questions that do not belong in a high-value reference page
- added questions on project purpose, command reliability, Ollama lifecycle behaviour, model selection, runtime configuration, contributor validation, and troubleshooting entry points

### Other Documentation Changes

- `README.md`: reclassified the FAQ as a shared reference and removed the obsolete illustrated interface references while keeping the animated gameplay demo
- `USER_GUIDE.md`: aligned the Ollama setting labels with the current UI wording and reframed the FAQ link as a cross-audience reference
- the overview docs: clarified the documentation split so the FAQ sits between the user guide and contributor guide instead of being treated as a purely user-facing page
- `CONTRIBUTING.md`: corrected the documented shutdown key to `stop_ollama_on_exit`, documented the legacy `auto_stop_ollama` fallback accurately, and added guidance on what belongs in the FAQ
- `docs/index.html`: updated the FAQ card description to match the new scope
- `CHANGELOG.md`: recorded the FAQ consolidation and README cleanup

### Follow-up Improvements Implemented

- added a compact compatibility matrix to `README.md` covering Python support, the current BatLLM version, and the expected Ollama workflow
- added a short release-bundle troubleshooting appendix to `README.md` for macOS, Linux, Windows, and generic launcher issues
- added a shared glossary to `README.md` for recurring terms such as `prompt augmentation`, `independent contexts`, `shared context`, and `last_served_model`
- added a lightweight documentation review checklist to the pull request workflow in `CONTRIBUTING.md`
- reordered the shared top-of-page documentation navigation so `README` is the first item
- removed the obsolete SVG interface diagrams from `docs/images/`

## Earlier Documentation Restructure Summary

### Scope

This section summarises the larger documentation restructuring completed earlier in the same documentation revision cycle.

### Main Changes

#### Audience Split

- kept `README.md` as the project overview and entry point for both users and contributors
- kept `USER_GUIDE.md` as the user-facing game manual
- consolidated developer-facing configuration, testing, and troubleshooting material into `CONTRIBUTING.md`

#### User Guide Rewrite

- rewrote `USER_GUIDE.md` to read like a game manual rather than a mixed reference page
- restored the screen recording in the guide
- restored and updated the match flow and rules material from the earlier documentation version
- retained the bot command reference, modes of play, screen descriptions, and Ollama usage details
- added a clearer tutorial path, screen-by-screen manual structure, and safety guidance around Ollama actions
- kept the text friendly and readable while aligning it with the current UI labels and workflow

#### Contributing Guide Rewrite

- rewrote `CONTRIBUTING.md` as a conventional developer and contribution manual
- grouped setup, architecture, configuration, testing, documentation workflow, coding conventions, and developer troubleshooting into one maintained guide
- removed the previous fragmentation across multiple developer-facing markdown files

#### Overview Alignment

- kept `README.md` as the overview page for both users and contributors
- updated the documentation landing page so it reflects the final split between the game manual and the developer manual
- kept the higher-level project framing and AI-literacy rationale visible in the overview documents

### Removed Files

The following obsolete standalone documentation files were removed because their content now lives in `CONTRIBUTING.md`:

- `docs/CONFIGURATION.md`
- `docs/TESTING.md`
- `docs/TROUBLESHOOTING.md`

The unused screenshot below was also removed:

- `docs/screenshots/before_starting.png`

### Navigation Cleanup

- removed links to the deleted standalone developer-reference pages from the primary markdown navigation bars
- updated `docs/index.html` so the primary cards reflect the current documentation model
- updated cross-references in the maintained docs to point to the new consolidated locations

## Retained Prior Material

The revision intentionally preserved key high-level material from the earlier documentation set, especially:

- the research and education framing of BatLLM
- the AI literacy motivation
- the human-vs-human, AI-mediated description of play
- the game flow and rules explanation
- the command reference and mode descriptions

## Validation

The docs were checked for stale references to the removed standalone pages after the earlier restructure and for scope consistency in the current FAQ consolidation pass.
