# Homebrew Packaging

BatLLM's Homebrew distribution is maintained as a source-based tap formula rather than as a Python package published to PyPI. The current generator and formula remain oriented around macOS on Apple Silicon.

The tap formula installs:

- the BatLLM source tree into Homebrew's `pkgshare`
- an isolated Python 3.12 virtual environment in `libexec/venv`
- offline-pinned Python resources resolved from `packaging/homebrew/requirements.txt`
- wrapper scripts for `batllm` and `batllm-analyzer`

The wrappers set `BATLLM_HOME` to a user-writable location by default:

- macOS: `$HOME/Library/Application Support/BatLLM`

That keeps BatLLM's mutable config and saved-session data out of the Homebrew cellar.

## Local Smoke Test

Generate a local worktree archive and a temporary formula file:

```bash
python create_homebrew_formula.py \
  --create-worktree-archive /tmp/BatLLM-homebrew-source.tar.gz \
  --formula-out /tmp/batllm.rb
```

Then test it with Homebrew:

```bash
brew tap-new --no-git local/batllm-smoke
cp /tmp/batllm.rb "$(brew --repository)/Library/Taps/local/homebrew-batllm-smoke/Formula/batllm.rb"
brew install local/batllm-smoke/batllm
brew test batllm
brew uninstall --force batllm
brew untap local/batllm-smoke
```

Recent Homebrew releases reject direct file-based formula installs outside a tap, so the temporary local tap flow is required for local install smoke tests.

## Tap Publish Workflow

Tagged releases can publish automatically to the shared `krahd/homebrew-tap` through the repository workflow. That workflow requires a repository secret named `HOMEBREW_TAP_TOKEN` with push access to `krahd/homebrew-tap`.

For manual maintainer updates, generate the formula after the source ref you want to install from is published on GitHub.

For a release tag:

```bash
python create_homebrew_formula.py \
  --github-tag v$(cat VERSION) \
  --formula-out /path/to/homebrew-krahd/Formula/batllm.rb
```

For a pushed branch while iterating:

```bash
python create_homebrew_formula.py \
  --github-branch homebrew-distribution \
  --formula-out /path/to/homebrew-krahd/Formula/batllm.rb
```

After writing the formula, validate it before committing the tap update:

```bash
brew audit --formula /path/to/homebrew-krahd/Formula/batllm.rb
brew install --build-from-source /path/to/homebrew-krahd/Formula/batllm.rb
brew test batllm
```

Use a release tag for the stable tap formula. Branch-based formula generation is intended only for pre-release validation.
