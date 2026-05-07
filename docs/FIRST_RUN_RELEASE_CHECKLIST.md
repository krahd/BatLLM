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

- checklist completed by maintainer:
- date:
- release candidate tag:
