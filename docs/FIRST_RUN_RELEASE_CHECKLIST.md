> ![BatLLM logo](./images/logo-small.png) **[Project](../README.md) · [Documentation](README.md) · [Release Criteria](RELEASE_CRITERIA_1_0.md) · [Status](../STATUS.md)**

# First-run and release-bundle checklist

Use a fresh machine, virtual machine, or disposable user profile for each release candidate. Record results in the release pull request or release issue rather than editing old execution logs into this reusable checklist.

## Release candidate

- Version/tag:
- Commit:
- Tester:
- Date:
- Platform and architecture:
- Python version:
- Installation channel:

## Fresh installation

- [ ] Install from the intended channel without using an existing BatLLM environment.
- [ ] Confirm the documented Python version is accepted.
- [ ] Confirm dependencies install without manual package substitutions.
- [ ] Launch the main application.
- [ ] Launch the standalone Game Analyzer.
- [ ] Confirm the application writes only to the expected state location.

## Ollama missing

- [ ] Launch BatLLM without the Ollama CLI available.
- [ ] Confirm the install prompt is understandable.
- [ ] Decline installation and confirm the application remains usable.
- [ ] Open **Ollama Config** and confirm **Install Ollama** remains available.

## Ollama installed but stopped

- [ ] Launch with automatic startup disabled and confirm the start prompt appears.
- [ ] Start Ollama from the application.
- [ ] Confirm status and output log update.
- [ ] Repeat with automatic startup enabled.
- [ ] Confirm the configured warm-up timeout is respected.

## Model workflow

- [ ] Refresh local models.
- [ ] Select an installed model and press **Use Selected**.
- [ ] Confirm successful warm-up updates the selected and last-served model values.
- [ ] Refresh remote models when network access is available.
- [ ] Download a disposable test model only when storage and network use are acceptable.
- [ ] Test deletion only with a disposable model and confirm the warning first.

## Game and history

- [ ] Submit one prompt per player and complete at least one turn.
- [ ] Complete a round and start another round.
- [ ] Start a new game and confirm previous model history does not leak into it.
- [ ] Confirm invalid model output is visible in History and does not crash the game.
- [ ] Confirm prompt augmentation and independent/shared context settings behave as documented.

## Save and analyzer

- [ ] Save a session after at least one completed turn.
- [ ] Confirm the file is written to the documented location.
- [ ] Load it in the in-app Game Analyzer.
- [ ] Load it in the standalone analyzer.
- [ ] Navigate games, rounds, turn starts, and individual plays.
- [ ] Confirm prompts, responses, commands, settings, model metadata, and state differences are readable.
- [ ] Confirm a legacy or malformed file is rejected clearly.

## Exit and recovery

- [ ] Verify exit confirmation when enabled.
- [ ] Verify save-on-exit prompting when enabled.
- [ ] Verify direct exit when both options are disabled.
- [ ] Verify service shutdown behaviour when automatic stop is enabled.
- [ ] Confirm save and service errors do not silently discard user input.

## Release bundle

- [ ] Run `python create_release_bundles.py`.
- [ ] Confirm the expected source and platform archives exist.
- [ ] Extract the native platform bundle into a path containing spaces.
- [ ] Run the included installer.
- [ ] Run the main application launcher.
- [ ] Run the analyzer launcher.
- [ ] Confirm writable-state behaviour matches `STATE_AND_INSTALLATION.md`.

## Homebrew on Apple Silicon macOS

- [ ] Generate a formula from the exact release source.
- [ ] Install it through a temporary local tap.
- [ ] Run `brew test batllm`.
- [ ] Launch `batllm` and `batllm-analyzer`.
- [ ] Confirm state is stored under `~/Library/Application Support/BatLLM` or an explicit override.
- [ ] Uninstall and untap cleanly.

## Final sign-off

- [ ] Protected workflows pass on the release commit.
- [ ] `python tools/check_docs.py` passes.
- [ ] Known failures and deferred checks are recorded explicitly.
- [ ] Version and release notes are consistent.
- [ ] Maintainer approves the release.
