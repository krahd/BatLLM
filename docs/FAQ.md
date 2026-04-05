> ![BatLLM logo](./images/logo-small.png) **[README](README.md) · [Overview](DOCUMENTATION.md) · [User Guide](USER_GUIDE.md) · [Contributing](CONTRIBUTING.md) · [FAQ](FAQ.md) · [Changelog](CHANGELOG.md) · [Credits](CREDITS.md) · [Code Docs](code/html/index.html)**

# FAQ

This FAQ is shared between advanced users and contributors. It focuses on recurring, non-trivial questions. Step-by-step screen walkthroughs live in [USER_GUIDE.md](USER_GUIDE.md), while setup, architecture, testing, and troubleshooting procedures live in [CONTRIBUTING.md](CONTRIBUTING.md).

## What is BatLLM actually for?

BatLLM is a local, AI-mediated, human-vs-human battle game and a research/education project. It is meant to make prompting, model behaviour, strategy, and failure modes concrete through play rather than to act as a generic chat shell.

## Is BatLLM a general-purpose inference server?

No. BatLLM depends on local LLM infrastructure, but it does not try to replace Ollama or provide a standalone inference platform.

## Is BatLLM strictly human-vs-human?

Yes. The current design assumes two human players, two bots, and no NPC opponent or single-player campaign mode.

## Why can a good strategy still fail in play?

The model has to translate the player's intent into BatLLM's strict command format. Prompt wording, model choice, context history, prompt augmentation, and shared-vs-independent contexts all affect whether a strategically sound idea becomes a valid in-game action.

## What role does Ollama play in BatLLM?

BatLLM uses the Python `ollama` client for gameplay chat requests. The `Ollama Config` screen uses the `ollama` CLI plus local HTTP endpoints for lifecycle actions, model inventory, downloads, deletions, and warm-up.

## What happens if Ollama is missing or not running?

If the CLI is missing, BatLLM can ask whether to launch the official installer. If Ollama is installed but stopped, BatLLM can ask whether to start it or skip the prompt and auto-start it when `Start Ollama Automatically on BatLLM Launch` is enabled.

## What is the difference between local and remote models?

- local models already exist in the local Ollama installation and can be selected for gameplay immediately
- remote models are names discovered from `https://ollama.com/library` and only become playable after download

## Does BatLLM change my real Ollama installation?

Yes. Starting or stopping the service, downloading models, deleting models, and reinstalling Ollama all affect the configured local Ollama environment. Treat the Ollama screen as a real system control surface, not a BatLLM-only sandbox.

## What does `Use Selected` change?

`Use Selected` writes the chosen model to `llm.model`, attempts to warm it for gameplay, and records it in `llm.last_served_model` after a successful warm-up. That saved value lets BatLLM restore the same served model the next time it starts Ollama.

## Can I review saved games later inside BatLLM?

Yes. Current `Save Session` exports are analyzer-compatible JSON files. You can open them from the in-app `Game Analyzer` button or from the standalone launcher `python run_game_analyzer.py`.

The analyzer replays game logic using the saved prompts, ordered plays, and the per-round `gameplay_settings_snapshot` embedded in the session file. Legacy top-level list exports are not replay-supported there.

## Can I manage Ollama outside BatLLM?

Yes. If Ollama is already installed, running, and reachable at the configured host and port, BatLLM can use it without the in-app control screen. The screen is recommended, not mandatory.

## Where is the runtime configuration stored?

The main runtime file is `src/configs/config.yaml`. Contributors should also know that `src/configs/app_config.py` defines fallback defaults used when keys are missing from the YAML.

## What should contributors validate before opening a pull request?

Run the relevant non-live tests for the area changed, keep cross-platform impact in mind, and update documentation in the same branch whenever UI labels, config keys, setup steps, or Ollama behaviour change. The current command set is documented in [CONTRIBUTING.md](CONTRIBUTING.md).

## Where should I start when something seems wrong?

Use the document that matches the problem:

- gameplay flow and screen behaviour: [USER_GUIDE.md](USER_GUIDE.md)
- recurring practical and architectural questions: [FAQ.md](FAQ.md)
- setup, configuration, testing, and troubleshooting: [CONTRIBUTING.md](CONTRIBUTING.md)

If the problem is model-related, inspect the History screen and the Ollama output log before assuming the game logic failed.
