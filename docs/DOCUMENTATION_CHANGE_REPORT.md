# Documentation Change Report

## Scope

This report summarises the documentation restructuring completed in the current revision.

## Main Changes

### Audience Split

- kept `README.md` as the project overview and entry point for both users and contributors
- kept `USER_GUIDE.md` as the user-facing game manual
- consolidated developer-facing configuration, testing, and troubleshooting material into `CONTRIBUTING.md`

### User Guide Rewrite

- rewrote `USER_GUIDE.md` to read like a game manual rather than a mixed reference page
- restored the screen recording in the guide
- restored and updated the match flow and rules material from the earlier documentation version
- retained the bot command reference, modes of play, screen descriptions, and Ollama usage details
- added a clearer tutorial path, screen-by-screen manual structure, and safety guidance around Ollama actions
- kept the text friendly and readable while aligning it with the current UI labels and workflow

### Contributing Guide Rewrite

- rewrote `CONTRIBUTING.md` as a conventional developer and contribution manual
- grouped setup, architecture, configuration, testing, documentation workflow, coding conventions, and developer troubleshooting into one maintained guide
- removed the previous fragmentation across multiple developer-facing markdown files

### Overview Alignment

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

The docs were checked for stale references to the removed standalone pages after the restructure.
