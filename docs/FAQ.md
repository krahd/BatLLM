> ![BatLLM logo](./images/logo-small.png) **[Overview](DOCUMENTATION.md) · [Readme](README.md) · [User Guide](USER_GUIDE.md) · [Contributing](CONTRIBUTING.md) · [FAQ](FAQ.md) · [Changelog](CHANGELOG.md) · [Credits](CREDITS.md) · [Code Docs](code/html/index.html)**

# FAQ

## Is BatLLM a general-purpose inference server?

No. BatLLM is a local game and educational project that happens to rely on local LLM infrastructure.

## Is BatLLM strictly human-vs-human?

Yes. The current game is designed around two human players whose actions are mediated through LLMs. BatLLM does not currently include NPC bots or a single-player mode.

## Does BatLLM use Ollama?

Yes. The current codebase uses:

- the Python `ollama` client for gameplay chat requests
- the `ollama` CLI and local HTTP endpoints for the Ollama configuration screen

## What is the difference between local models and remote models?

- local models are already present in your local Ollama installation
- remote models are names discovered from `https://ollama.com/library` and are only usable after download

## How do I close the model list popup?

The local and remote model pickers close when you:

- press `Esc`
- click outside the popup
- click the popup `Close` button

## What happens if Ollama is not installed?

If the app cannot start Ollama because the CLI is missing, the Ollama screen opens an install-guidance flow. BatLLM does not auto-install Ollama for you.

## What happens if the remote model list cannot be loaded?

The Ollama screen shows an error in its status/output area and leaves the current selection state unchanged. Typical causes are no network access or a failure reaching `https://ollama.com/library`.

## Does BatLLM change my real Ollama installation?

Yes. The current Ollama screen operates on the real local Ollama service and model store configured by `llm.url` and `llm.port`.

## Does deleting a model only remove BatLLM's reference?

No. `Delete Selected` deletes the local Ollama model itself.

## Does downloading a model only affect BatLLM?

No. `Download Selected` pulls the model into the shared local Ollama installation. Other local tools that use the same Ollama store can see that model afterward.

## Can BatLLM stop models that are already running?

When you choose a model with `Use Selected`, BatLLM may stop the previously managed BatLLM model before warming the newly selected one. It does not claim ownership of every model that may already be running outside BatLLM.

## Can I use BatLLM without the Ollama screen?

Yes. If your Ollama setup is already running and reachable at the configured host, you can manage Ollama externally and simply use BatLLM for gameplay.

## How does prompt augmentation help?

Prompt augmentation gives the model explicit, structured game-state context on each turn. In practice that can make model output more relevant and interpretable, but it still depends on the quality of the player's prompt and the model's ability to follow command-format constraints.

## Why does the app ask about exit confirmation or saving?

Those behaviours are controlled by the Settings screen values:

- `Confirm on Exit`
- `Prompt to Save on Exit`

## Does the history screen support `Esc` to go back?

Not currently. The history screen uses its explicit `Back` button.

## Where should I look for setup or runtime failures?

Start with [USER_GUIDE.md](USER_GUIDE.md) for normal usage questions, or [CONTRIBUTING.md](CONTRIBUTING.md) if you need the consolidated developer troubleshooting notes.
