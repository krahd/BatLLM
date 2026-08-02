# AGENTS.md

Operating instructions for coding agents working in this repository.

## Repository purpose

BatLLM is a Python/Kivy research, education, and game project for exploring AI-mediated play, prompt quality, model behaviour, and local-model workflows. Preserve the project's practical, critical, and educational framing while keeping the application reliable across supported platforms.

## Canonical documentation

- `README.md`: public project overview and installation.
- `docs/README.md`: documentation index.
- `docs/USER_GUIDE.md`: user-facing game and application manual.
- `docs/CONTRIBUTING.md`: development setup, architecture, validation, and release work.
- `docs/ROADMAP.md`: product direction.
- `docs/RELEASE_CRITERIA_1_0.md`: release gates.
- `docs/CHANGELOG.md`: chronological history.
- `STATUS.md`: concise current project snapshot.

Review the relevant documents before changing behaviour, setup, configuration, tests, packaging, or repository structure.

## STATUS.md upkeep

`STATUS.md` must describe the current repository, not accumulate a PR-by-PR audit diary.

Update it whenever a change affects:

- current capabilities or architecture;
- supported platforms, Python versions, dependencies, or configuration;
- validation state;
- known limitations or risks;
- release readiness;
- important paths or repository structure; or
- pending and longer-term work.

Keep historical detail in `docs/CHANGELOG.md`, the pull request, or a dedicated research audit document.

`STATUS.md` should remain readable in one sitting and include, where relevant:

- project purpose and release phase;
- current capabilities;
- setup and validation commands;
- architecture summary;
- configuration and state behaviour;
- important files;
- recent durable changes;
- current validation evidence;
- known limitations;
- pending and longer-term work.

Timestamp contract:

- Put `Last updated: YYYY-MM-DD HH:MM` near the top.
- Repeat the exact same line as the final line.
- Use local wall-clock time in `America/Chicago`, the repository's maintained status timezone.
- A missing, stale, or mismatched timestamp is a documentation error.

Use a small Mermaid or text diagram only when it makes the current architecture easier to understand. Do not preserve obsolete diagrams or expand the status page merely to record diagram-edit history.

## Development rules

- Inspect relevant source, tests, configuration, and documentation before editing.
- Prefer focused changes over broad rewrites unless the task explicitly asks for restructuring.
- Preserve public behaviour and compatibility unless the change intends otherwise.
- Do not delete user-authored work or evidence without understanding its purpose.
- Remove generated artefacts, caches, one-off migration payloads, and temporary automation once they are no longer needed.
- Do not commit secrets, credentials, private data, machine-specific absolute paths, or user state.
- Use British English in maintained prose documentation.
- Keep release and version references consistent with `VERSION` and `CITATION.cff`.

## Safety

BatLLM can affect a real local Ollama installation and real saved sessions.

- Preserve confirmation prompts for destructive or expensive actions.
- Do not weaken safeguards around model deletion, downloads, service control, session handling, or configuration writes.
- Tests must use an isolated temporary `BATLLM_HOME` and must not mutate repository defaults or user configuration.
- Treat `python run_tests.py full` and install-level packaging checks as stateful operations requiring explicit maintainer intent.

## Validation

Run the narrowest checks that cover the change, then broaden when shared behaviour may be affected.

Typical commands:

```bash
python run_tests.py core
python run_tests.py non-live
python tools/check_docs.py
python -m pylint src run_batllm.py run_game_analyzer.py \
  create_release_bundles.py create_homebrew_formula.py
```

For public API documentation changes, regenerate Doxygen intentionally and inspect the generated diff.

Only report checks that were actually run. Record significant unrun manual or stateful validation in `STATUS.md`.

## Documentation rules

- Keep each page within its defined role.
- Avoid duplicating full configuration files, test logs, or release histories across pages.
- Link to the source of truth when content is likely to drift.
- Update UI labels, commands, paths, schema versions, and workflow descriptions with the code change that affects them.
- Run `python tools/check_docs.py` after documentation or repository-structure changes.

## Git hygiene

- Check the worktree before and after edits.
- Do not revert unrelated user changes.
- Stage only intended paths.
- Use a branch and pull request unless the user explicitly requests another workflow.
- Do not leave temporary workflows, marker files, downloaded artefacts, or patch payloads in the final tree.

## Communication style

Use terse factual progress updates. Do not use playful filler, metaphors, or fake enthusiasm. State findings, changes, validation, and blockers directly.
