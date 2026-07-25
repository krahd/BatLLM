<p align="center">
  <img src="docs/images/logo-small.png" alt="BatLLM logo" width="160">
</p>

# BatLLM

BatLLM is a local, two-player battle game in which each player controls a bot by prompting a large language model. Players do not move, rotate, shield, or shoot directly. They write instructions; the models translate those instructions into the small command language understood by the game.

The project is both playable software and a research and teaching instrument. It makes prompt quality, model behaviour, context design, system configuration, and failure visible through play.

![BatLLM gameplay demonstration](docs/screenshots/quick_demo.gif)

## Current state

| | |
| --- | --- |
| Repository version | `0.3.6` |
| Python | `3.10`, `3.11`, or `3.12` (`3.12` recommended) |
| Platforms | macOS, Linux, and Windows |
| Model runtime | Local Ollama, accessed through `modelito` |
| Game mode | Two human players, two model-mediated bots |
| Analysis | Saved-session review in the built-in or standalone Game Analyzer |
| Licence | MIT |

The current `main` branch is protected by multiplatform, dependency, and research-validation workflows. See [STATUS.md](STATUS.md) for the current project snapshot and remaining release work.

## How the game is organised

- A **session** is one execution of the application.
- A session can contain one or more **games**.
- A game contains one or more **rounds**.
- At the start of a round, each player submits the prompt that will guide their bot during that round.
- A round contains a sequence of **turns**. In each turn, both bots may execute one command, unless the game ends first.

Two settings change the prompting conditions:

- **Independent contexts** gives each bot a separate model conversation.
- **Prompt augmentation** prepends structured game-state information to the player's prompt.

## Install and run

### Homebrew on Apple Silicon macOS

```bash
brew tap krahd/tap
brew install krahd/tap/batllm
batllm
```

Launch the standalone analyser with:

```bash
batllm-analyzer
```

### From source

```bash
git clone https://github.com/krahd/BatLLM.git
cd BatLLM
python3 -m venv .venv_BatLLM
source .venv_BatLLM/bin/activate
python -m pip install -r requirements.txt
python run_batllm.py
```

On Windows PowerShell, activate the environment with:

```powershell
.\.venv_BatLLM\Scripts\Activate.ps1
```

Launch the standalone analyser from a source checkout with:

```bash
python run_game_analyzer.py
```

BatLLM requires a local Ollama installation for normal play. The application can open the official installer and can start, stop, and manage the configured local Ollama service.

> [!CAUTION]
> BatLLM's Ollama controls operate on the real local Ollama installation. Starting or stopping Ollama, downloading a model, or deleting a model can affect other tools on the same machine.

## First game

1. Launch BatLLM.
2. Open **Settings**, then **Ollama Config**.
3. Start Ollama and select an installed model. Download one first when necessary.
4. Return to the home screen.
5. Each player writes and submits a prompt.
6. The round begins automatically after both prompts are ready.
7. Review the result in **History**, then revise the prompts for the next round.

The model must return one valid command per action. The recognised commands are documented in the [User Guide](docs/USER_GUIDE.md).

## Documentation

- [Documentation index](docs/README.md)
- [User Guide](docs/USER_GUIDE.md)
- [FAQ](docs/FAQ.md)
- [Contributing](docs/CONTRIBUTING.md)
- [Current project status](STATUS.md)
- [Roadmap](docs/ROADMAP.md)
- [Changelog](docs/CHANGELOG.md)
- [Security policy](SECURITY.md)

## Research and educational framing

BatLLM supports experiential learning about prompting and local models while keeping the social, political, and economic conditions of generative AI in view. The game is designed to encourage both practical experimentation and critical discussion rather than presenting prompting as a neutral technical skill.

BatLLM began with support from the University of Colorado Boulder's 2024 Arts & Humanities Grant Program and later received a CHA Small Grant. See [Credits](docs/CREDITS.md).

## Author and citation

BatLLM was initiated by [Tomas Laurenzo](https://laurenzo.net). Citation metadata is available in [CITATION.cff](CITATION.cff).
