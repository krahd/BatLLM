> ![BatLLM logo](./images/logo-small.png) **[Project](../README.md) · [Documentation](README.md) · [User Guide](USER_GUIDE.md) · [Contributing](CONTRIBUTING.md) · [Status](../STATUS.md)**

# Installation channels and mutable state

BatLLM does not yet use one identical state location for every installation channel. This page records the behaviour implemented today.

## Source checkout

When `BATLLM_HOME` is not set:

- the shipped and mutable configuration path is `src/configs/config.yaml`;
- a relative `data.saved_sessions_folder` resolves from the repository root; and
- configuration changes therefore modify the checkout.

This is convenient for development but is not suitable for a read-only package installation.

## `BATLLM_HOME`

When `BATLLM_HOME` is set:

- shipped defaults still come from `src/configs/config.yaml`;
- mutable configuration is written to `$BATLLM_HOME/config.yaml`; and
- relative saved-session folders resolve below `$BATLLM_HOME`.

The directory is created as needed. Tests use this mechanism with a temporary directory.

## Homebrew

The generated Homebrew wrappers set:

```bash
BATLLM_HOME="$HOME/Library/Application Support/BatLLM"
```

unless the environment already supplies another value. This keeps mutable state outside the Homebrew cellar.

## Release bundles

The current Windows, macOS, and Linux release-bundle launchers run from the extracted bundle directory and do not set `BATLLM_HOME` automatically.

Consequences:

- configuration changes can modify the extracted bundle's `src/configs/config.yaml`;
- relative saved-session folders remain inside the extracted bundle; and
- users who want a separate writable state directory should set `BATLLM_HOME` before launching.

Moving release bundles to automatic platform-specific user-state directories remains a release-hardening task.

## Default platform paths

`src/util/paths.py` defines default user-state paths for future or packaging use:

- macOS: `~/Library/Application Support/BatLLM`
- Windows: `%APPDATA%\BatLLM` when `APPDATA` is available
- Linux and other Unix systems: `~/.local/share/BatLLM`

The application does not currently activate these defaults automatically for ordinary source or release-bundle launches; `BATLLM_HOME` must be set by the launcher or user.

## Invariants

- Tests must use an isolated temporary `BATLLM_HOME`.
- Homebrew must not write into the cellar.
- Configuration and session writes must remain atomic.
- Documentation must distinguish shipped defaults from the active mutable path.
- Changes to state-location behaviour require migration and release-bundle tests.
