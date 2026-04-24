> ![BatLLM logo](./images/logo-small.png) **[README](README.md) · [User Guide](USER_GUIDE.md) · [Contributing](CONTRIBUTING.md) · [FAQ](FAQ.md) · [Changelog](CHANGELOG.md) · [Credits](CREDITS.md) · [Releases](https://github.com/krahd/BatLLM/releases)**

# BatLLM 1.0 Release Criteria

This checklist turns the roadmap's 1.0 goals into explicit release gates.

A 1.0 candidate is ready only when all sections below are complete.

## 1) CI and Branch Protection Gates

Required checks on `main` pull requests:

- `Multiplatform Validation / test`
- `Multiplatform Validation / homebrew`
- `Multiplatform Validation / smoke`

Required workflow expectations:

- non-live suite passes on Linux, macOS, and Windows
- Homebrew dry-run formula rendering and packaging tests pass
- smoke payload checks pass against the mock Ollama server

## 2) Product Reliability Gates

Must be verified by tests and spot checks:

- startup flow covers missing Ollama, stopped Ollama, and auto-start paths
- timeout handling remains deterministic and user-recoverable
- malformed or incomplete model responses do not crash gameplay flow
- save/load and analyzer replay compatibility remain stable for v2 sessions

## 3) UX Consistency Gates

Must be complete for both gameplay and analyzer modes:

- navigation and key actions are consistent between screens
- control and status panel structure follows one visual system
- labels and button language are aligned in maintained docs

## 4) First-Run and Bundle Gates

Must be validated per platform release bundle:

- launcher scripts open the expected app mode
- first-run config behavior is correct with and without `BATLLM_HOME`
- startup guidance for Ollama install/start paths remains accurate

## 5) Documentation Gates

The maintained doc set must be in sync:

- `README.md` and `USER_GUIDE.md` reflect current UX
- `CONTRIBUTING.md` reflects current CI/test/release workflow
- `CHANGELOG.md` has the release notes for the shipped 1.0 delta

## Suggested Sign-off Process

Before tagging `v1.0.0`:

1. freeze scope to 1.0 roadmap items only
2. run all required CI checks on the release branch
3. run the first-run checklist in `FIRST_RUN_RELEASE_CHECKLIST.md`
4. run Homebrew publish as a dry-run via formula generation
5. tag and publish only after all checkboxes are complete
