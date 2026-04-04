> ![BatLLM logo](./images/logo-small.png) **[Overview](DOCUMENTATION.md) · [Readme](README.md) · [User Guide](USER_GUIDE.md) · [Contributing](CONTRIBUTING.md) · [FAQ](FAQ.md) · [Changelog](CHANGELOG.md) · [Credits](CREDITS.md) · [Code Docs](code/html/index.html)**

# BatLLM Documentation

BatLLM is a local, AI-mediated, human-vs-human battle game built with Kivy. Two human players write prompts, two bots execute model-driven commands, and the game board resolves movement, shields, bullets, rounds, and match state.

BatLLM is also a free and libre open source research and education project. It uses a deliberately simple game form to make prompting, strategic thinking, model limitations, and human-AI mediation concrete rather than abstract. Players do not directly control the bots; instead, they must work through AI systems that know nothing about the game and must be guided through language.

## Project Aims

BatLLM is intended to do more than provide a toy interface for local models. The project aims to:

- support practical and critical AI literacy through hands-on, self-directed play
- make prompt-writing a situated strategic activity rather than an isolated exercise
- expose both the capabilities and the shortcomings of LLM-mediated interaction
- encourage broader social understanding of AI, including the power, access, political, and economic asymmetries that shape generative AI systems

In that sense, BatLLM treats play as a research and teaching method. It is a game, but also a framework for learning how AI systems behave, where they fail, and how people adapt to those limits.

This documentation set is now split by audience:

- project overview and entry point: [README.md](README.md)
- user-facing guidance: [USER_GUIDE.md](USER_GUIDE.md) and [FAQ.md](FAQ.md)
- developer-facing guidance: [CONTRIBUTING.md](CONTRIBUTING.md)
- project history and attribution: [CHANGELOG.md](CHANGELOG.md) and [CREDITS.md](CREDITS.md)

## Documentation Scope

This main page focuses on the project as a whole: its motivations, aims, current product shape, and the relationship between the maintained guides. The README remains the overview page for both users and contributors, the user guide stays user-facing, and the contributing guide now consolidates configuration, testing, troubleshooting, and development workflow.

## Current Product Snapshot

The current application includes four primary screens:

1. `HomeScreen`: prompt entry, prompt history, session save/load, round control, and the game board.
2. `SettingsScreen`: gameplay values, context mode, prompt augmentation, and exit-flow settings.
3. `HistoryScreen`: compact per-bot prompt history plus full session history.
4. `OllamaConfigScreen`: local Ollama service controls plus local/remote model management.

The Ollama screen is now the recommended operational workflow for most users. It can:

1. start Ollama through `start_ollama.sh`
2. stop Ollama through `stop_ollama.sh`
3. refresh local models from `/api/tags`
4. choose the active BatLLM model from a modal picker
5. refresh remote models from `https://ollama.com/library`
6. download a selected remote model with confirmation
7. delete a selected local model with confirmation

The model pickers are modal popups. They close when the user:

- presses `Esc`
- clicks outside the popup
- clicks the popup `Close` button

## Runtime Architecture

At runtime, BatLLM is organised around a small set of cooperating components:

- `HomeScreen` and the `.kv` layouts own the main user interface.
- `GameBoard` owns the live game world and turn/round flow.
- `Bot` instances hold bot state and execute commands.
- `OllamaConnector` builds chat requests and talks to the Python `ollama` client against the configured host.
- `HistoryManager` is the single source of truth for recorded game and chat history.
- `OllamaConfigScreen` manages the local Ollama server and model inventory for BatLLM.

The gameplay path uses the configured Ollama chat endpoint (`llm.path`, default `/api/chat`) and sends a full `messages` history on each call. The model-management path in the Ollama screen uses the local REST endpoints (`/api/tags`, `/api/ps`, `/api/pull`, `/api/generate`) together with the `ollama` CLI.

## Release Notes

See [CHANGELOG.md](CHANGELOG.md) for the running release history.

Highlights in the current documentation revision:

- the docs now reflect the actual `Ollama Config` workflow and labels
- the model-picker behaviour is documented, including `Esc` and outside-click dismissal
- developer-facing configuration, testing, and troubleshooting have been consolidated into the contributing guide
- the install docs now match the Python dependency set used by the codebase
- the documentation homepage no longer needs to redirect to the repository root

## Code Documentation

Generated API documentation lives under [code/html/index.html](code/html/index.html).

Regenerate it from the repository root with:

```bash
doxygen docs/code/dox_config.properties
```

## Safety Notes

BatLLM operates on a real local Ollama installation. The app can:

- start or stop the Ollama server on the configured host and port
- change BatLLM's configured active model
- download additional local models
- delete local models

If other tools on the same machine use the same Ollama installation, treat the Ollama screen as a shared system control surface, not a BatLLM-only sandbox.
