> ![BatLLM logo](./images/logo-small.png) **[Overview](DOCUMENTATION.md) · [Readme](README.md) · [User Guide](USER_GUIDE.md) · [Contributing](CONTRIBUTING.md) · [FAQ](FAQ.md) · [Changelog](CHANGELOG.md) · [Credits](CREDITS.md) · [Code Docs](code/html/index.html)**

# BatLLM

BatLLM is a free and libre open source research project, education tool, and, at its core, a game: a simple, human-vs-human, turn-based battle game. The game does not expose direct interaction mechanisms for play. Instead, players must utilise AI systems to act on their behalf. Those AIs, think of ChatGPT-like systems running locally, do not know anything about the game. Deploying effective gaming strategies through AI-mediated interaction is the players' task.

Like every other area where AI is used, having the best strategy for the game world alone is not enough to win. By combining language, strategy, and AI-driven gameplay, BatLLM aims to offer a fun, safe, self-directed, independent, and hands-on platform for exploring the strengths and shortcomings of LLMs.

In a world increasingly shaped by AI, and marked by profound asymmetries of power, knowledge, and access, developing critical and practical AI literacy is both urgent and necessary.

The project aims to support a broader social understanding of AI by pairing intuitive play with experiential learning. It hopes to contribute to the development of AI prompting skills while highlighting the need for critical engagement with the social, political, and economic dynamics deeply embedded in generative AI systems.

The project is intentionally practical: the point is not just to watch an LLM respond to prompts, but to make prompt quality, model behaviour, context design, and system configuration materially affect the outcome of play.

This README is the overview page for the project. It keeps the core framing of BatLLM, gives a brief getting-started path, and points both users and contributors to the right documentation.

> [!IMPORTANT]
> BatLLM began as part of a project supported by the [2024 Arts & Humanities Grant Program](https://www.colorado.edu/researchinnovation/2024/05/03/seventeen-arts-humanities-projects-receive-grants-advance-scholarship-research-and) of the [Research & Innovation Office](https://www.colorado.edu/researchinnovation/) at the University of Colorado Boulder.

![BatLLM demo](./screenshots/quick_demo.gif)

## What Is In The App

BatLLM currently ships with:

1. a main gameplay screen for prompt entry and round control
2. a settings screen for gameplay and exit-flow options
3. a history screen for prompt and response review
4. an Ollama configuration screen for local service and model management

## Documentation Map

### User-Facing

- [USER_GUIDE.md](USER_GUIDE.md): the game manual, including rules, match flow, screens, modes, commands, and Ollama usage
- [FAQ.md](FAQ.md): short answers to common practical questions

### Developer-Facing

- [CONTRIBUTING.md](CONTRIBUTING.md): the developer and contribution manual, including setup, architecture, configuration, testing, and troubleshooting

### Project-Level

- [DOCUMENTATION.md](DOCUMENTATION.md): project aims, motivations, and documentation structure
- [CHANGELOG.md](CHANGELOG.md): notable documentation and release changes
- [CREDITS.md](CREDITS.md): project attribution and support context
- [code/html/index.html](code/html/index.html): generated API reference

## Requirements

### Supported Platforms

BatLLM is now maintained for:

- macOS
- Linux
- Windows

### System Requirements

1. Python 3.10 or newer. Python 3.11 or 3.12 is recommended.
2. A local Ollama installation if you want to run BatLLM with the default workflow.
3. Hardware capable of running the local model you choose.

### Python Dependencies

The repository Python environment uses `requirements.txt`, which now includes the packages the current code imports, including `requests` and the Python `ollama` client.

### Ollama Requirements

BatLLM uses both:

- the Python `ollama` package during gameplay
- the `ollama` CLI for the in-app start/stop/version workflow and helper scripts

If the CLI is missing, the app can show install guidance, but it does not install Ollama automatically.

## Quick Start

Clone the repository, create a virtual environment, install the Python dependencies, and launch the app.

On macOS and Linux:

```bash
git clone https://github.com/krahd/BatLLM.git
cd BatLLM
python3 -m venv .venv_BatLLM
source .venv_BatLLM/bin/activate
pip install -r requirements.txt
python run_batllm.py
```

On Windows:

```powershell
git clone https://github.com/krahd/BatLLM.git
cd BatLLM
py -m venv .venv_BatLLM
.\.venv_BatLLM\Scripts\Activate.ps1
pip install -r requirements.txt
python run_batllm.py
```

Install Ollama separately using the official download page for your platform:

- macOS: `https://ollama.com/download`
- Linux: `https://ollama.com/download/linux`
- Windows: `https://ollama.com/download/windows`

### Release Bundles

BatLLM now ships with a cross-platform release-bundle generator:

```bash
python create_release_bundles.py
```

That command creates:

- source-code archives
- a Windows bundle with `.bat` install and run launchers
- a macOS bundle with `.command` install and run launchers
- a Linux bundle with `.sh` install and run launchers

## Recommended Ollama Workflow

The default operational path is inside the app:

1. launch BatLLM
2. open `Settings`
3. click `Ollama Config`
4. use the Ollama screen to start Ollama, select a local model, and download or delete models as needed

The `Local Models` and `Remote Models` controls open modal pickers. Those pickers:

- refresh their data before opening
- render the model names in white text
- highlight the current selection
- use tightly packed rows with no gap between adjacent model entries
- close on `Esc`
- close when the user clicks outside the popup

Remote models are loaded from `https://ollama.com/library`.

### Local vs Remote Models

- local models already exist in your Ollama installation and can be selected immediately
- remote models are only candidates for download; they are not usable until pulled locally

### What `Use Selected` Does

Choosing a local model and pressing `Use Selected` updates `llm.model` in `src/configs/config.yaml`. BatLLM then attempts to make that model available for gameplay. If BatLLM previously started a different model itself, it may stop that earlier managed model before warming the newly selected one.

Behind the UI, BatLLM now uses a cross-platform Python helper for Ollama lifecycle management. The legacy shell scripts remain as Unix-friendly wrappers around that helper.

## Safety

> [!WARNING]
> BatLLM is provided as-is. The Ollama screen operates on your real local Ollama installation.

> [!CAUTION]
> If other tools use the same Ollama installation, BatLLM can affect them by starting or stopping the server, downloading models, deleting models, or switching the model BatLLM itself uses.

Destructive or expensive actions are guarded by confirmation prompts where implemented, but the effects are still real:

- `Download Selected` downloads a local Ollama model
- `Delete Selected` deletes a local Ollama model
- `Start Ollama` and `Stop Ollama` control the configured local service

## Screens At A Glance

### Home

The home screen is where players:

- write and submit prompts
- browse prompt history
- load and save prompt text
- start new games
- open settings and history

Pressing `Esc` on the home screen enters the configured exit flow. Depending on the settings, BatLLM may:

- ask for exit confirmation
- ask whether to save the session before exit
- exit immediately

### Settings

The settings screen controls:

- rounds, turns, health, damage, shield size, and step length
- independent vs shared model contexts
- prompt augmentation
- `Confirm on Exit`
- `Prompt to Save on Exit`

The button that opens the Ollama screen is labeled `Ollama Config`.

### History

The history screen shows:

- a compact, per-bot history pane
- a full session history pane

It currently uses an explicit `Back` button to return to the home screen.

### Ollama Config

The Ollama screen shows:

- current Ollama status
- a multi-line output log
- local model controls
- remote model controls

Illustrated references:

![Ollama control screen diagram](./images/ollama-control-screen.svg)
![Local model picker diagram](./images/local-model-picker.svg)
![Remote model picker diagram](./images/remote-model-picker.svg)

## For Contributors

If you are working on the codebase rather than using the app, start with [CONTRIBUTING.md](CONTRIBUTING.md). That guide now consolidates the developer-facing material that used to be split across configuration, testing, and troubleshooting pages.
