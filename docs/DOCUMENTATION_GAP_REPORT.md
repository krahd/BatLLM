# Documentation Gap Report

Date: 2026-04-03

## Scope Reviewed

- `docs/README.md`
- `docs/USER_GUIDE.md`
- `docs/DOCUMENTATION.md`
- `docs/CONTRIBUTING.md`
- `docs/FAQ.md`
- `docs/CREDITS.md`
- `docs/index.html`
- generated docs under `docs/code/`

## Release-Critical Changes Needed

1. `docs/index.html` should stop redirecting to the GitHub repository root and instead land on the documentation entry point.
   The published docs currently have no real homepage.

2. `docs/DOCUMENTATION.md` is still a placeholder.
   It needs a real release-level overview of the current product, especially the in-app Ollama workflow and the current gameplay architecture.

3. `docs/CONTRIBUTING.md` contains outdated implementation details.
   It still describes LLM communication as `requests.post` / `UrlRequest` driven plain-text calls, while the current runtime uses the Python `ollama` client, `/api/chat`, centralized message history, and an Ollama control screen.

4. Installation documentation is not trustworthy in its current form.
   `docs/README.md` and `docs/USER_GUIDE.md` say `pip install -r requirements.txt` is the setup path, but the running code imports `requests` and `ollama` and those packages are not listed in `requirements.txt`.
   Either the dependency list must be fixed before release, or the docs must explicitly disclose the extra required packages.

5. The Ollama Control Screen documentation is incomplete for the current UX.
   The docs mention selecting, downloading, and deleting models, but they do not describe that model lists open in a modal picker, can now be dismissed with `Esc` or outside-click, refresh when opened, and visually highlight the current selection.

6. The generated code docs are stale relative to the current UI surface.
   The generated output under `docs/code/` does not cover `OllamaConfigScreen`, so the published API docs omit one of the main user-facing screens.

## Existing Docs That Should Be Updated

### `docs/README.md`

- Update the Ollama Control Screen section to describe the actual list-picker behavior:
  modal presentation, `Esc` dismissal, outside-click dismissal, and selection highlighting.
- Add a note that the remote model list is fetched from `https://ollama.com/library`.
- Clarify the distinction between:
  choosing a local model,
  downloading a remote model,
  and deleting a local model.
- Replace or supplement the current demo media with at least one screenshot or GIF of the Ollama screen.
- Add a release note or short changelog entry for the new model-picker behavior.

### `docs/USER_GUIDE.md`

- Expand the Ollama Control Screen walkthrough into a step-by-step task flow:
  open screen, refresh local models, choose a model, download from remote list, delete a model, close the picker.
- Document `Esc` behavior consistently across screens:
  Home screen exit flow, Settings return, Ollama picker dismissal, History return.
- Add the exit-related settings that are currently undocumented:
  `Confirm on Exit` and `Prompt to Save on Exit`.
- Add a short explanation of what happens when BatLLM changes the active local model:
  the app may preload the selected model and may stop the previously managed one.

### `docs/CONTRIBUTING.md`

- Rewrite the architecture section to match the current codebase:
  `OllamaConnector`, `/api/chat`, centralized `HistoryManager`, and the Ollama configuration screen.
- Replace the current testing section with the real non-live test command used in this repo.
- Document the headless Kivy test setup needed in CI or local terminal-only environments.
- Note that generated docs must be regenerated when new screens or modules are added.

### `docs/FAQ.md`

- Add operational questions for the current Ollama workflow:
  what happens if Ollama is not installed,
  what happens if the remote model list cannot be loaded,
  whether BatLLM changes the shared local Ollama instance,
  and how to close the model picker.
- Add a question explaining the difference between local models and remote models.
- Add a question clarifying that deleting a model removes the local Ollama model itself, not just a BatLLM reference.

### `docs/DOCUMENTATION.md`

- Replace the placeholder text with a proper project overview.
- Add a release summary for the current version.
- Add a navigation section that points readers to user docs, developer docs, config reference, and generated API docs.

## New Documentation That Should Be Added

1. A dedicated configuration reference.
   This should document the keys in `src/configs/config.yaml`, especially:
   `llm.model`, `llm.url`, `llm.port`, `llm.path`, `llm.timeout`, `llm.num_ctx`,
   the system-instruction file paths,
   `ui.confirm_on_exit`,
   and `ui.prompt_save_on_exit`.

2. A dedicated testing guide.
   The current `run_tests.sh` modes are too limited to explain the actual non-live workflow that developers need.

3. A short release notes or changelog file.
   The project currently has no obvious place to record user-visible changes such as the Ollama model-picker behavior.

4. Troubleshooting documentation.
   This should cover:
   missing Ollama CLI,
   remote-library fetch failures,
   dependency/setup mismatches,
   and side effects on an existing local Ollama installation.

5. Visual documentation for the Ollama screen.
   At minimum:
   one screenshot of the screen itself,
   one screenshot of the local-model picker,
   and one screenshot of the remote-model picker.

## Recommended Documentation Order

1. Fix the install/dependency documentation mismatch.
2. Replace the placeholder main docs page.
3. Update README and USER_GUIDE for the actual Ollama workflow and new picker behavior.
4. Update CONTRIBUTING with the real architecture and test flow.
5. Add config reference and troubleshooting material.
6. Regenerate and republish code docs so the Ollama screen is covered.
