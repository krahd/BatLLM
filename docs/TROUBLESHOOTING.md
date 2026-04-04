> ![BatLLM logo](./images/logo-small.png) **[Overview](DOCUMENTATION.md) · [Readme](README.md) · [User Guide](USER_GUIDE.md) · [Configuration](CONFIGURATION.md) · [Testing](TESTING.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Contributing](CONTRIBUTING.md) · [FAQ](FAQ.md) · [Changelog](CHANGELOG.md) · [Credits](CREDITS.md) · [Code Docs](code/html/index.html)**

# Troubleshooting

## The App Cannot Start Ollama

Symptoms:

- `Start Ollama` fails
- the output log says `ollama not found`
- the install-guidance dialog appears

What to check:

1. confirm the `ollama` CLI is installed and available on your `PATH`
2. run `ollama --version` in a terminal
3. verify `llm.url` and `llm.port` in `src/configs/config.yaml`

## BatLLM Launches But Gameplay Fails To Talk To The Model

BatLLM gameplay uses the Python `ollama` package plus the configured chat endpoint.

Check:

1. `pip install -r requirements.txt` completed successfully
2. the virtualenv contains the `ollama` Python package
3. `llm.path` is correct for the server you are using
4. the configured model name in `llm.model` exists locally

## The Remote Model List Will Not Load

The remote picker fetches model names from `https://ollama.com/library`.

If refresh fails:

1. verify the machine has outbound network access
2. retry from the Ollama screen
3. check the Ollama screen output log for the captured error

Existing local selections are preserved if the remote refresh fails.

## The Local Model List Is Empty

The local picker loads from `/api/tags` on the configured Ollama host.

Check:

1. Ollama is actually running on `llm.url:llm.port`
2. `ollama list` shows models in the same installation
3. the configured host and port point to the intended local service

## I Downloaded Or Deleted A Model And Another Tool Was Affected

That is expected. BatLLM's Ollama screen works against the shared local Ollama installation, not a BatLLM-specific sandbox.

## The Model Picker Does Not Stay Open

The picker is intentionally modal and closes when:

- `Esc` is pressed
- the user clicks outside the popup
- the popup `Close` button is pressed

## Doxygen Output Is Stale

Regenerate the code docs from the repo root:

```bash
doxygen docs/code/dox_config.properties
```

## Kivy Tests Fail In A Headless Shell

Use the headless environment variables from [TESTING.md](TESTING.md):

```bash
KIVY_WINDOW=mock KIVY_NO_ARGS=1 KIVY_NO_CONSOLELOG=1 KIVY_HOME=/tmp/batllm-kivy PYTHONPATH=src ./.venv_BatLLM/bin/python -m pytest -q src/tests/test_ollama_config_screen.py src/tests/test_ollama_config_screen_logic.py
```

## `run_tests.sh core` Does Not Cover My UI Change

That is expected. `core` only runs the lightweight smoke checks. Use the non-live unit suite from [TESTING.md](TESTING.md) for screen and dialog changes.
