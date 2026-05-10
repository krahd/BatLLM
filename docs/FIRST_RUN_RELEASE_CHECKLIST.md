> ![BatLLM logo](./images/logo-small.png) **[README](README.md) · [User Guide](USER_GUIDE.md) · [Contributing](CONTRIBUTING.md) · [FAQ](FAQ.md) · [Changelog](CHANGELOG.md) · [Credits](CREDITS.md) · [Releases](https://github.com/krahd/BatLLM/releases)**

# First-Run and Release Bundle Checklist

Use this checklist before each release candidate.

## Environment Matrix

- macOS (Apple Silicon)
- Linux
- Windows

## Validation Steps

### A. Fresh Clone and Install

- create a new virtual environment
- install `requirements.txt`
- confirm `python run_batllm.py` launches
- confirm `python run_game_analyzer.py` launches

### B. First-Run Without Ollama Installed

- verify startup prompts for install path are shown
- verify declining install keeps app usable
- verify `Ollama Config` still exposes install action

### C. First-Run With Ollama Installed But Stopped

- verify startup prompt to start service appears when auto-start is off
- verify auto-start path works when setting is on
- verify selected or fallback startup model behavior is correct

### D. Save/Load and Analyzer

- play and save at least one session
- load the session in analyzer mode
- verify timeline/round navigation and prompts display correctly

### E. Release Bundles

- run `python create_release_bundles.py`
- verify generated launchers exist for main app and analyzer on all platforms
- launch from each wrapper and confirm expected entrypoint behavior

### F. Homebrew (maintainer path)

- render formula from worktree:
  - `python create_homebrew_formula.py --create-worktree-archive /tmp/BatLLM-homebrew-source.tar.gz --formula-out /tmp/batllm.rb`
- confirm packaging tests pass:
  - `python -m pytest -q src/tests/test_homebrew_packaging.py`

## Sign-off

- checklist completed by maintainer: in progress (Copilot-assisted local run)
- date: 2026-05-09
- release candidate tag: v0.3.6-rc1

## Current Execution Record (2026-05-08)

- macOS: command-level checks completed (`create_release_bundles.py`, Homebrew formula render, Homebrew packaging tests, `run_tests.py full`).
- Linux: pending manual first-run checklist execution on a Linux host.
- Windows: pending manual first-run checklist execution on a Windows host.
- Release policy note: keep the project on the `0.x` line pending maintainer testing sign-off.

## Current Execution Record (2026-05-09)

- Re-ran the full automated validation stack locally: `pytest -q` (`151 passed, 2 skipped`) and `python run_tests.py full` (`4 passed` core smoke; `153 passed` full).
- Re-ran packaging/release automation locally: `python create_release_bundles.py`, Homebrew formula generation to `/tmp/batllm.rb`, `python -m pytest -q src/tests/test_homebrew_packaging.py` (`7 passed`), and `python validate_packaging_smoke.py` (passed).
- Reconfirmed `main` branch protection required checks: `ubuntu-latest`, `windows-latest`, `macos-latest`, `Homebrew dry-run`, `Smoke: Ollama integration`.
- Linux: still pending manual first-run checklist execution on a Linux host.
- Windows: still pending manual first-run checklist execution on a Windows host.
