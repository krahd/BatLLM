> ![BatLLM logo](./images/logo-small.png) **[Project](../README.md) · [Documentation](README.md) · [User Guide](USER_GUIDE.md) · [Contributing](CONTRIBUTING.md) · [Status](../STATUS.md)**

# Installation channels and mutable state

Configuration preferences use a writable user directory for source checkouts, Homebrew installations, and release bundles. Shipped defaults remain in `src/configs/config.yaml` and are read only by configuration persistence.

## Configuration paths

When `BATLLM_HOME` is set, preferences are saved to `$BATLLM_HOME/config.yaml`. Otherwise the platform default is used:

- macOS: `~/Library/Application Support/BatLLM/config.yaml`
- Windows: `%APPDATA%\BatLLM\config.yaml`, falling back to `~/AppData/Roaming/BatLLM/config.yaml`
- Linux and other Unix systems: `~/.local/share/BatLLM/config.yaml`

The directory is created on save. Loading does not create a file. Values are loaded in order: built-in fallbacks, shipped YAML, then the user YAML. Existing user preferences take precedence, including custom sections. Writes are atomic, and explicit attempts to save over shipped defaults are rejected.

Homebrew wrappers already set the macOS `BATLLM_HOME` default. Release-bundle launchers need no environment override to save preferences outside the extracted bundle.

## Temporary settings

**Set Temporarily** applies an execution-only overlay to the settings used by the game. Preference saves triggered by model selection, last-served metadata or timeout edits exclude that overlay. **Set as Defaults** explicitly writes the chosen settings and replaces those temporary values. Reloading configuration clears execution overrides.

## Existing preferences and upgrades

Existing `$BATLLM_HOME/config.yaml` files continue to load in place. If an older source checkout or extracted bundle contains customised `src/configs/config.yaml` values, they still load as the base configuration and are copied into the user configuration on the next save. The legacy file is not rewritten.

Before updating or replacing an older checkout or bundle, preserve its customised YAML: copy it to the user configuration path above if that path does not already exist. If a user configuration already exists, retain it and merge only the desired legacy values into it. Do not reset the old checkout YAML before preserving its settings. Settings already overwritten by an earlier update cannot be recovered by the loader.

## Saved sessions

Relative saved-session folders now resolve below the same user directory as preferences, with `BATLLM_HOME` taking precedence. Absolute paths are unchanged. On default-directory access, legacy JSON sessions in the checkout or bundle are copied into the user directory without moving originals or overwriting existing files. Conflicting filenames remain available at their original path through the analyser file chooser. Explicit `BATLLM_HOME` installations retain their existing directory and do not import checkout saves.

## Invariants

- Tests must use an isolated temporary `BATLLM_HOME`.
- Homebrew must not write into the cellar.
- Configuration and session writes must remain atomic.
- Documentation must distinguish shipped defaults from the active mutable path.
- Changes to state-location behaviour require migration and release-bundle tests.
