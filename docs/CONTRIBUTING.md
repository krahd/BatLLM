> ![BatLLM logo](./images/logo-small.png) **[Overview](DOCUMENTATION.md) · [Readme](README.md) · [User Guide](USER_GUIDE.md) · [Configuration](CONFIGURATION.md) · [Testing](TESTING.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Contributing](CONTRIBUTING.md) · [FAQ](FAQ.md) · [Changelog](CHANGELOG.md) · [Credits](CREDITS.md) · [Code Docs](code/html/index.html)**

# Contributing

This guide is for contributors who want to change BatLLM's code, tests, or documentation.

## Contribution Expectations

- keep pull requests scoped to one topic
- use English commit messages
- explain non-obvious behavior changes in the pull request description
- update docs when the user-facing workflow, setup path, configuration, or tests change

## Local Setup

### Python Environment

```bash
git clone https://github.com/krahd/BatLLM.git
cd BatLLM
python -m venv .venv_BatLLM
source .venv_BatLLM/bin/activate
pip install -r requirements.txt
```

### Ollama Environment

The codebase depends on two different Ollama surfaces:

- the Python `ollama` package for gameplay chat requests
- the `ollama` CLI for the local service-management helpers and the Ollama config screen

For non-live unit work, the CLI is not required. For live gameplay or `run_tests.sh full`, it is required.

## Project Layout

Core runtime modules:

- `src/main.py`: Kivy app entrypoint
- `src/view/`: screens and `.kv` layouts
- `src/game/game_board.py`: match flow, rendering hooks, and UI coordination
- `src/game/bot.py`: bot state and command execution
- `src/game/ollama_connector.py`: chat/history request builder using the Python `ollama` client
- `src/game/history_manager.py`: authoritative game and chat history
- `src/configs/`: YAML config files and config loader
- `start_ollama.sh` and `stop_ollama.sh`: local Ollama helper scripts

Maintained documentation:

- `docs/README.md`
- `docs/USER_GUIDE.md`
- `docs/CONFIGURATION.md`
- `docs/TESTING.md`
- `docs/TROUBLESHOOTING.md`
- `docs/CHANGELOG.md`

Generated API docs:

- `docs/code/`

## Runtime Architecture

The current gameplay stack works like this:

1. `HomeScreen` owns the high-level UI and delegates game actions to `GameBoard`.
2. `GameBoard` owns the active `Bot` instances, the prompt store, and the live round/turn flow.
3. `Bot` instances execute movement, rotation, shield, and bullet actions.
4. `GameBoard` uses `OllamaConnector` to send synchronous chat requests through the Python `ollama` client.
5. `HistoryManager` records game history and chat history as the single source of truth.

The current model-management stack works like this:

1. `OllamaConfigScreen` checks server state using local HTTP endpoints such as `/api/version`, `/api/ps`, and `/api/tags`.
2. It uses `start_ollama.sh` and `stop_ollama.sh` for service lifecycle actions.
3. It uses `https://ollama.com/library` as the remote-library source for downloadable model names.
4. It uses `/api/pull` and `/api/generate` for pull and preload operations.

## Testing

See [TESTING.md](TESTING.md) for the full matrix.

Most contributor work should use the non-live suite in a headless Kivy environment:

```bash
KIVY_WINDOW=mock KIVY_NO_ARGS=1 KIVY_NO_CONSOLELOG=1 KIVY_HOME=/tmp/batllm-kivy PYTHONPATH=src ./.venv_BatLLM/bin/python -m pytest -q src/tests/test_history_compact.py src/tests/test_close_prompt_behavior.py src/tests/test_utils_confirmation_dialog.py src/tests/test_ollama_config_screen.py src/tests/test_ollama_config_screen_logic.py
```

Quick smoke coverage:

```bash
./run_tests.sh core
```

Live Ollama smoke coverage:

```bash
./run_tests.sh full
```

## Documentation Maintenance

When behavior changes, update the maintained docs in the same branch. In particular, update docs when you change:

- UI labels
- setup steps
- config keys or defaults
- test commands
- Ollama model-management behavior
- keyboard and exit behavior

Regenerate the API docs when public modules or screens change:

```bash
doxygen docs/code/dox_config.properties
```

## Code Style

- use Python 3 style annotations where practical
- keep Kivy screen logic in the screen classes and layout structure in `.kv` files
- avoid undocumented user-facing behavior changes
- prefer clear state transitions over hidden side effects

## Pull Request Checklist

Before opening a PR:

1. run the relevant tests
2. update docs if the workflow or UI changed
3. regenerate code docs if public modules or screen docs changed
4. review the resulting diff for generated-file noise before pushing
