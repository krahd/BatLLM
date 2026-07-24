> ![BatLLM logo](./images/logo-small.png) **[Project](../README.md) · [Documentation](README.md) · [Contributing](CONTRIBUTING.md) · [Release Checklist](FIRST_RUN_RELEASE_CHECKLIST.md) · [Status](../STATUS.md)**

# Maintainer audit checklist

Use this compact checklist after changes to launchers, paths, configuration, session formats, packaging, dependencies, or Ollama lifecycle code.

## Repository hygiene

- [ ] No temporary workflows, marker files, downloaded artefacts, patch payloads, or one-off migration directories are tracked.
- [ ] `README.md`, `STATUS.md`, and the relevant role-specific documentation are current.
- [ ] `VERSION`, `CITATION.cff`, and release-facing references agree.
- [ ] `python tools/check_docs.py` passes.

## Automated validation

- [ ] `python run_tests.py non-live` passes.
- [ ] Python compilation passes.
- [ ] The maintained Pylint gate passes.
- [ ] Packaging tests pass when packaging changed.
- [ ] Research validation passes when trace, replay, schema, or research files changed.
- [ ] Dependency audit and review pass when dependencies changed.

## State and safety

- [ ] Tests use a temporary `BATLLM_HOME`.
- [ ] Homebrew does not write to the cellar.
- [ ] Source and release-bundle state behaviour is documented accurately.
- [ ] Configuration and session writes remain atomic.
- [ ] Destructive model actions remain confirmed.
- [ ] Subprocesses use explicit arguments, bounded waits, and understandable errors.

## Platform and manual checks

- [ ] CI passes on Ubuntu, macOS, and Windows.
- [ ] Paths containing spaces are covered.
- [ ] Missing, stopped, and non-responsive Ollama states are handled.
- [ ] Main application and analyzer receive manual GUI smoke checks before a release.
- [ ] Live Ollama and install-level package tests are run only with explicit maintainer intent.
