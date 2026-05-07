# AGENTS.md

Canonical guidance for automated coding agents working in this repository.
These instructions are intended to be directly usable by GitHub Copilot, OpenAI Codex, Claude, and other compatible agents.

Compatibility note:

- This file is the source of truth for agent behavior in this repository.
- Tool-specific compatibility files may point here, but this document must remain complete on its own.

## Project Shape

BatLLM is a Python/Kivy local-LLM game application with two main user-facing surfaces:

- the main BatLLM gameplay app launched through `run_batllm.py`
- the read-only game analyzer launched through `run_game_analyzer.py`

The repository also includes packaging helpers, documentation, and test coverage for local runtime behavior.

The LLM/Ollama integration should be implemented through `modelito` functionality. Keep BatLLM-specific logic in BatLLM, but do not reintroduce generic Ollama lifecycle, model-management, or provider behavior that `modelito` already provides.

## Important Paths

- `run_batllm.py`: primary launcher for the app
- `run_game_analyzer.py`: launcher for the analyzer surface
- `src/main.py`: main Kivy application entrypoint
- `src/game/`: gameplay logic, connectors, replay/session data
- `src/view/`: Kivy screens and dialogs
- `src/llm/`: BatLLM LLM integration layer and BatLLM-specific runtime facade over `modelito`
- `src/configs/`: app config handling and configurator tooling
- `src/tests/`: pytest coverage
- `docs/`: user and maintainer documentation
- `STATUS.md`: complete current project status report; mandatory upkeep

## Development Rules

- Prefer focused edits over broad rewrites or formatting churn.
- Preserve existing public behavior unless the task explicitly changes it.
- Keep generic Ollama/provider behavior in `modelito`; BatLLM should call into it rather than duplicate it.
- Do not add backward-compatibility wrappers unless they solve a current in-repo need. This repository is pre-release; prefer the direct architecture.
- When changing model-management behavior, update both runtime code and the affected documentation.
- Do not commit generated artifacts, cache folders, build outputs, logs, or temporary files.
- Keep Homebrew/package-facing behavior aligned with the shipped docs and requirements.

## STATUS.md Mandatory Upkeep

`STATUS.md` must be kept up to date at all times.

After every non-trivial change, investigation result, bug fix, feature, refactor, validation update, or release-relevant doc update, update `STATUS.md` in the same work session.

`STATUS.md` is required to be a complete project status report. At minimum it must include:

- current state and active focus
- what changed recently
- validation performed and validation gaps
- known risks, limitations, or open issues
- next prioritized steps

Timestamp requirement:

- include a top-level timestamp line using this format: `Last updated: YYYY-MM-DD HH:MM`
- include the same `Last updated: YYYY-MM-DD HH:MM` line again at the very bottom of `STATUS.md` as a footer
- use the user's local wall-clock time and timezone context
- never leave the timestamp stale when the report content changes

Agents must not mark work complete until `STATUS.md` accurately reflects the project state.

## Validation

Run the narrowest checks that cover the change first, then broaden when the change touches shared flows.

Common commands for this repository:

```bash
pytest -q
/Users/tom/devel/ml-llm/llm/BatLLM/.venv_BatLLM/bin/python run_tests.py full
```

For packaging-sensitive changes, also validate the relevant packaging script or build flow that was touched.

Document what was run and what was not run in `STATUS.md`.

## Documentation Expectations

When runtime behavior, package requirements, model-management behavior, or UX changes, update the relevant docs in the same change set. Typically this includes:

- `docs/README.md` or root overview docs when install/runtime expectations change
- `docs/USER_GUIDE.md` for user-visible model/runtime behavior
- `docs/CHANGELOG.md` when the change is release-relevant
- `STATUS.md`

## Git Hygiene

- Check `git status --short` before and after edits.
- Do not revert user-authored changes unless explicitly asked.
- Keep commits atomic and stage only intended paths when the worktree is mixed.
- Commit or push only when explicitly requested.
