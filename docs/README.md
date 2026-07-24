> ![BatLLM logo](./images/logo-small.png) **[Project](../README.md) · [Documentation](README.md) · [User Guide](USER_GUIDE.md) · [FAQ](FAQ.md) · [Contributing](CONTRIBUTING.md) · [Status](../STATUS.md) · [Releases](https://github.com/krahd/BatLLM/releases)**

# BatLLM documentation

This directory contains the maintained documentation for BatLLM. Each page has one primary purpose so that setup instructions, game rules, development notes, release planning, and historical records do not compete with one another.

## Start here

| You need to… | Read… |
| --- | --- |
| understand the project or install it | [Project README](../README.md) |
| play a first game or understand the rules | [User Guide](USER_GUIDE.md) |
| answer a recurring practical question | [FAQ](FAQ.md) |
| work on the codebase | [Contributing](CONTRIBUTING.md) |
| see what is currently working or still pending | [STATUS.md](../STATUS.md) |
| report a vulnerability | [Security policy](../SECURITY.md) |

## User documentation

- [User Guide](USER_GUIDE.md): installation choices, first game, game structure, commands, screens, saved sessions, the Game Analyzer, and Ollama controls.
- [FAQ](FAQ.md): concise answers to questions that recur across play and development.
- [Credits](CREDITS.md): authorship, institutional context, and funding support.

## Contributor documentation

- [Contributing](CONTRIBUTING.md): development setup, architecture, configuration, tests, CI, packaging, release work, and troubleshooting.
- [Installation channels and mutable state](STATE_AND_INSTALLATION.md): where configuration and sessions are written in source, packaged, Homebrew, and test environments.
- [Maintainer audit checklist](MAINTAINER_AUDIT_CHECKLIST.md): compact pre-release and high-risk-change checks.
- [Homebrew packaging](../packaging/homebrew/README.md): formula generation, local tap validation, and publication.

## Project and release planning

- [Roadmap](ROADMAP.md): the remaining local-desktop work and the planned networked architecture.
- [1.0 release criteria](RELEASE_CRITERIA_1_0.md): release gates rather than release notes.
- [First-run and release checklist](FIRST_RUN_RELEASE_CHECKLIST.md): manual validation to perform on release candidates.
- [UI unification plan](UI_UNIFICATION_PLAN_1_0.md): the remaining interface-consistency work.
- [Changelog](CHANGELOG.md): historical and unreleased changes.

## Research documentation

The implementation and reproducibility material for the URUCON 2026 work is under [research/urucon2026](../research/urucon2026/README.md). The editable manuscript is intentionally maintained in the separate `academic-writing` repository; this repository contains the software and research artefact only.

## Current support summary

- Python `3.10`–`3.12`; Python `3.12` is recommended.
- macOS, Linux, and Windows source and release-bundle workflows.
- Apple Silicon macOS Homebrew formula.
- Local Ollama model runtime through `modelito`.
- Saved-session schema v2 for the user-facing Game Analyzer.
- Schema v3 for the headless URUCON research runtime and verifier.

The repository version is recorded in [`VERSION`](../VERSION). Current validation and unresolved manual checks are recorded once, in [STATUS.md](../STATUS.md), rather than repeated throughout the documentation.
