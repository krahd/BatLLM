> ![BatLLM's logo](./images/logo-small.png) **[Readme](README.md) &mdash; [Documentation](DOCUMENTATION.md) &mdash; [User Guide](USER_GUIDE.md) &mdash; [Contributing](CONTRIBUTING.md) &mdash; [FAQ](FAQ.md) &mdash; [Credits](CREDITS.md)**

# User Guide

## What BatLLM Is

BatLLM is a local, AI-mediated, human-vs-human battle game. Two human players write prompts, two LLM-backed bots interpret those prompts, and the bots act inside the game arena.

From a user perspective, the project includes:

1. The main game screen for prompt entry and gameplay.
2. A settings screen for round, turn, and gameplay parameters.
3. A history screen for reviewing LLM input and output.
4. An Ollama Control Screen for starting and stopping Ollama, selecting models, downloading models, and deleting models.

> [!WARNING]
> BatLLM is provided as-is. It can change your local Ollama state, including active model selection, model inventory, and whether the Ollama server is running.
>
> [!CAUTION]
> If the same Ollama installation is used by other projects on your machine, be careful. Downloading or deleting models in BatLLM can affect those other projects too.

## Mini Demo

The screen recording below shows the basic interaction flow: players input a prompt and submit it to their bot. When both players have done so a new round begins.

Prompts can be loaded and saved to the filesystem, or can be fetched from the bot's history of submitted prompts.

To see actual I/O with the LLM you can open the History Screen, and to change the game's parameters you can use the Settings Screen.

![Demo Gif](./screenshots/quick_demo.gif)

## Setup and First Run

The recommended setup path is:

1. Clone the repository.
2. Create and activate a Python virtual environment.
3. Install dependencies.
4. Launch BatLLM.
5. Open the Ollama Control Screen from Settings and manage Ollama there.

Typical setup commands:

```bash
git clone https://github.com/krahd/batllm.git
cd batllm
python -m venv .venv_BatLLM
source .venv_BatLLM/bin/activate
pip install -r requirements.txt
python src/main.py
```

Manual Ollama installation is optional. If Ollama is missing, BatLLM can guide you through the in-app flow.

## Screens Overview

### Main Screen

Use the main screen to:

1. Write or load prompts for both players.
2. Start rounds and advance gameplay.
3. Watch the bots move, rotate, shield, and fire.
4. Access Settings and History.

### Settings Screen

Use the Settings screen to adjust:

1. Total rounds.
2. Turns per round.
3. Initial health.
4. Bullet damage.
5. Shield size.
6. Bot step length.
7. Independent or shared contexts.
8. Prompt augmentation.

### History Screen

Use the History screen to inspect the prompt and response history recorded during play. This is the best place to understand what each model received and how it responded.

### Ollama Control Screen

The Ollama Control Screen is available from Settings and is the default way to manage the local Ollama environment for BatLLM.

It supports:

1. Starting Ollama.
2. Stopping Ollama.
3. Refreshing available local models.
4. Choosing the active local model for BatLLM.
5. Refreshing remote models that can be downloaded.
6. Downloading a selected model with confirmation.
7. Deleting a selected local model with confirmation.

If Ollama does not start, BatLLM asks for a path and shows install guidance instead of trying to install software automatically.

> [!CAUTION]
> The Ollama Control Screen operates on your actual local Ollama installation. Deleting a model there deletes the local model itself, which can break other local tools or projects that rely on that model.

## Game Flow and Rules

A match consists of one or more rounds; each round consists of several turns. The game flow is as follows:

1. **Before the Round:**
   Both players are prompted to enter a new prompt for their bots. Once both players have submitted their prompts, the round begins.

2. **During Each Turn:**

    - At the start of each turn, the game randomly selects which player’s bot will act first for that turn. This random order is determined once per round.
    - The first bot’s prompt, augmented or raw depending on settings, is sent to the LLM, which returns a command to be immediately executed by the bot in the game world.
    - If the command is to fire, the entire lifespan of the bullet is part of the turn execution. A bullet travels until it hits the other bot or goes out of bounds.
    - A bullet that hits a bot outside its shield reduces the target bot's health by the configured bullet damage. Because damage resolution is part of the turn, the round may end abruptly.
    - Next, the second bot’s prompt is sent to its LLM, and that bot executes its command unless the round already ended.
    - This completes one turn.

3. **End of Round / Match:**

    - If a bot’s health reaches zero at any point, the match ends immediately. There is no respawning.
    - If neither bot is destroyed and the predefined number of turns in the round elapses, the round ends automatically. A popup shows the round results. If multiple rounds are enabled and both bots are still alive, the next round can begin.

Between rounds, players have the opportunity to adjust their strategy by writing new prompts. This is a key part of BatLLM’s educational value: you can analyze what the LLM did in the prior round and modify your prompt to guide it differently in the next round.

## Bot Commands Reference

| Code       | Action                                                       | Example |
| ---------- | ------------------------------------------------------------ | ------- |
| `C{angle}` | **Rotate clockwise** by `angle` degrees.                     | `C90`   |
| `A{angle}` | **Rotate anticlockwise** by `angle` degrees.                 | `A45`   |
| `M{step}`  | **Move forward** by one step of `step` length.               | `M0.3`  |
| `M{step}`  | **Move forward** by one step of default size.                | `M`     |
| `S1`       | **Raise shield**. Remains up until changed.                  | `S1`    |
| `S0`       | **Lower shield**. Remains down until changed.                | `S0`    |
| `S`        | **Toggle shield**: raises if down, lowers if up.             | `S`     |
| `B`        | **Shoot**: If its shield is lowered, fires one bullet.       | `B`     |

_Any other output from the LLM is interpreted as 'do nothing' this turn._

## Modes and Variations

- **Standard Mode:** Each player writes a prompt at the beginning of a round and the prompt is sent as-is to the LLM.
- **Prompt Augmentation:** The game can augment the player's prompt with game rules and structured game-state information.
- **LLM Context:**
    - _Independent Context:_ Each player has an isolated prompt/response history.
    - _Shared Context:_ Both bots share a single history, which can introduce interference between player strategies.

**Note:** There are no NPC bots. BatLLM is strictly AI-mediated human-vs-human play, where gameplay decisions originate in human-written prompts and are then carried out by LLMs.

## Configuration

BatLLM can be configured via a YAML file (`src/configs/config.yaml`). Command-line parameters are not currently implemented.

> [!IMPORTANT]
> Avoid modifying this file while BatLLM is running.

**YAML configuration file:**

Please see the repository's [../src/configs/config.yaml](../src/configs/config.yaml) file for the exact format and contents.

The most important user-facing configuration areas are:

1. Game values such as rounds, turns, health, damage, shield size, and step length.
2. Prompt augmentation and shared versus independent histories.
3. LLM endpoint values such as URL, port, path, and active model.

## Warnings and Disclaimer

1. BatLLM is offered as-is, without warranties or guarantees.
2. The Ollama Control Screen changes your real local Ollama environment.
3. Deleting or replacing models in BatLLM can interfere with other projects that use the same Ollama installation.
4. You should review model-management actions carefully before confirming them.

For deeper technical details, see the main documentation and README in this directory.
