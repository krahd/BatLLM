> ![BatLLM logo](./images/logo-small.png) **[Project](../README.md) · [Documentation](README.md) · [Roadmap](ROADMAP.md) · [Release Checklist](FIRST_RUN_RELEASE_CHECKLIST.md) · [Status](../STATUS.md)**

# BatLLM 1.0 release criteria

BatLLM remains on the `0.x` line. This document defines the gates for a future stable local-desktop 1.0 release; it is not a claim that the gates have already been completed.

## Automated gates

A release candidate must pass the protected `main` workflows:

- **CI**: Python `3.10`–`3.12` on Ubuntu, macOS, and Windows, including the complete non-live suite and the maintained Pylint gate.
- **Multiplatform Validation**: platform release-bundle generation, Homebrew dry-run tests, and mock-Ollama integration smoke.
- **Python dependency audit**.
- **Dependency review** when the dependency graph is available.
- **URUCON research validation** when research-facing paths change.
- **Documentation check** through `python tools/check_docs.py`.

No required check may be bypassed for release tagging.

## Product reliability gates

- Missing, stopped, slow, and non-responsive Ollama states have understandable recovery paths.
- Malformed model output cannot crash or corrupt the game lifecycle.
- Game transitions cannot inherit conversation history or stale asynchronous callbacks from previous games.
- Session saving is atomic and exports only completed analyzer-valid turns.
- Current v2 sessions load and replay deterministically in the Game Analyzer.
- Unsupported legacy sessions fail with a clear compatibility message.
- Configuration and session paths are correct for source, Homebrew, and release-bundle use.

## User-interface gates

- Equivalent actions use consistent labels across gameplay and analyzer screens.
- Back, cancel, and `Esc` behaviour is predictable and documented.
- Critical errors and destructive actions are visible and confirmed.
- The remaining work in [UI_UNIFICATION_PLAN_1_0.md](UI_UNIFICATION_PLAN_1_0.md) is either completed or explicitly deferred with maintainer sign-off.

## Native first-run gates

The [first-run checklist](FIRST_RUN_RELEASE_CHECKLIST.md) must be completed on:

- macOS;
- Linux; and
- Windows.

For each platform, verify:

- clean installation;
- missing-Ollama flow;
- installed-but-stopped flow;
- normal model selection and one complete game;
- session save and analyzer load;
- launcher behaviour; and
- writable-state behaviour.

Apple Silicon macOS additionally requires install-level Homebrew validation.

## Documentation gates

- `README.md` reflects the supported install paths and current product.
- `docs/USER_GUIDE.md` matches the game rules and UI labels.
- `docs/CONTRIBUTING.md` matches the code structure, CI, and release workflow.
- `STATUS.md` contains a current snapshot rather than historical audit logs.
- `docs/CHANGELOG.md` distinguishes released history from current development.
- Local links and the status timestamp contract pass `python tools/check_docs.py`.

## Sign-off

Before tagging `v1.0.0`:

1. Freeze scope to the signed-off 1.0 gates.
2. Run all protected workflows on the exact release commit.
3. Complete and record the native first-run checklist.
4. Complete live Ollama and Homebrew checks on machines where their side effects are acceptable.
5. Review version references in `VERSION`, `CITATION.cff`, the changelog, release notes, and generated packages.
6. Tag only after explicit maintainer approval.
