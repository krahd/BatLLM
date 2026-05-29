## Summary

This PR implements the confirmed high-confidence improvements from the BatLLM audit:

- adds a repository security policy;
- adds Dependabot for Python and GitHub Actions dependencies;
- adds PR-time dependency review;
- adds scheduled and PR-time Python dependency auditing with `pip-audit`;
- adds a cross-platform Python CI matrix for Linux, macOS, and Windows;
- documents the single runtime-state invariant: installed application files are read-only and mutable state belongs under `BATLLM_HOME` or the platform app-data equivalent;
- adds a maintainer audit checklist for launchers, configuration, sessions, Ollama lifecycle, and release checks.

## Rationale

The audit found that BatLLM has several operational surfaces: source launchers, analyzer launchers, Homebrew packaging, release bundles, mutable configuration, saved sessions, and local Ollama orchestration. This makes repository hygiene and state-location consistency critical.

This PR is deliberately additive. It avoids speculative refactors where source-level verification is required, but it establishes the CI/security/doc baseline needed before deeper changes such as entry-point consolidation, `pyproject.toml` migration, and state-path refactoring.

## Verification

Expected checks:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python run_tests.py
python -m compileall .
pylint src run_batllm.py run_game_analyzer.py create_release_bundles.py create_homebrew_formula.py
pip-audit -r requirements.txt
```

## Follow-up work

- Convert runtime configuration writes to use `BATLLM_HOME` everywhere.
- Add migration logic for repository-relative historical config.
- Collapse launchers onto canonical installed entry points.
- Add `pyproject.toml` after confirming package/module names under `src/`.
- Add tests for path handling, missing Ollama, non-responsive Ollama, subprocess timeouts, and session migration.
