> ![BatLLM logo](./images/logo-small.png) **[Overview](DOCUMENTATION.md) · [Readme](README.md) · [User Guide](USER_GUIDE.md) · [Configuration](CONFIGURATION.md) · [Testing](TESTING.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Contributing](CONTRIBUTING.md) · [FAQ](FAQ.md) · [Changelog](CHANGELOG.md) · [Credits](CREDITS.md) · [Code Docs](code/html/index.html)**

# Testing

BatLLM has three practical test tiers:

1. shell/config smoke checks
2. headless non-live unit tests
3. live Ollama smoke tests

## Environment

Use the project virtualenv:

```bash
source .venv_BatLLM/bin/activate
```

For terminal-only environments, run Kivy tests headlessly:

```bash
export KIVY_WINDOW=mock
export KIVY_NO_ARGS=1
export KIVY_NO_CONSOLELOG=1
export KIVY_HOME=/tmp/batllm-kivy
export PYTHONPATH=src
```

## Quick Smoke

`run_tests.sh core` currently runs only the lightweight smoke checks in `src/tests/test_history_compact.py`:

```bash
./run_tests.sh core
```

That covers:

- config shape
- shell-script syntax
- source compilation

## Recommended Non-Live Unit Suite

This is the most useful day-to-day test command for UI and logic changes:

```bash
KIVY_WINDOW=mock KIVY_NO_ARGS=1 KIVY_NO_CONSOLELOG=1 KIVY_HOME=/tmp/batllm-kivy PYTHONPATH=src ./.venv_BatLLM/bin/python -m pytest -q src/tests/test_history_compact.py src/tests/test_close_prompt_behavior.py src/tests/test_utils_confirmation_dialog.py src/tests/test_ollama_config_screen.py src/tests/test_ollama_config_screen_logic.py
```

That suite covers:

- exit-flow behavior
- confirmation and text-input dialogs
- Ollama config screen logic
- model-picker behavior
- non-live smoke checks

## Live Ollama Smoke

`run_tests.sh full` starts Ollama, runs the full `src/tests` suite with live Ollama smoke enabled, and then stops Ollama:

```bash
./run_tests.sh full
```

Equivalent environment toggle for the live smoke tests:

```bash
BATLLM_RUN_OLLAMA_SMOKE=1 PYTHONPATH=src ./.venv_BatLLM/bin/python -m pytest -q src/tests
```

Use this only when:

- the Ollama CLI is installed
- the configured host/port are available
- you are comfortable with BatLLM starting and stopping the configured local Ollama service

## Documentation Validation

When docs or API surface change:

```bash
doxygen docs/code/dox_config.properties
```

Review the generated diff under `docs/code/` before committing.

## What To Run For Common Changes

| Change type | Minimum recommended validation |
| --- | --- |
| gameplay logic | non-live unit suite |
| exit flow or dialogs | non-live unit suite |
| Ollama config screen | non-live unit suite |
| shell scripts | `./run_tests.sh core` |
| Ollama integration path | non-live unit suite plus live smoke if possible |
| docs only | regenerate code docs if public API docs changed |
