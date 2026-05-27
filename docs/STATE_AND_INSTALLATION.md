# Installation channels and mutable state

BatLLM should use one state model across all installation channels.

## Invariant

Installed application files are read-only at runtime. User changes must not mutate the source tree, package installation directory, Homebrew cellar, application bundle, or release-bundle program directory.

Runtime state belongs in a per-user application directory. `BATLLM_HOME` overrides the default location and is the canonical mechanism for tests, portable bundles, and package-manager integrations.

## State categories

| Category | Mutable | Location |
|---|---:|---|
| Packaged defaults | No | repository/package data |
| Effective configuration | Yes | `$BATLLM_HOME/config.yaml` or platform app-data equivalent |
| Saved sessions | Yes | `$BATLLM_HOME/sessions/` |
| Logs | Yes | `$BATLLM_HOME/logs/` |
| Cache/temp files | Yes | `$BATLLM_HOME/cache/` |

## Required behaviour

- On first run, create the user state directory if it does not exist.
- Copy packaged default configuration into the user state directory before applying user edits.
- Treat repository-relative `src/configs/config.yaml` as a read-only default, not as runtime state.
- Prefer atomic writes for configuration and saved sessions.
- Do not write to the Homebrew cellar or any other package-manager-controlled directory.
- Tests should set `BATLLM_HOME` to a temporary directory.

## Migration rule

If an older install has user-edited configuration in a repository-relative path, migrate it once into the user state directory and leave the original file untouched after migration.
