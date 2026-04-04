> ![BatLLM logo](./images/logo-small.png) **[Overview](DOCUMENTATION.md) · [Readme](README.md) · [User Guide](USER_GUIDE.md) · [Configuration](CONFIGURATION.md) · [Testing](TESTING.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Contributing](CONTRIBUTING.md) · [FAQ](FAQ.md) · [Changelog](CHANGELOG.md) · [Credits](CREDITS.md) · [Code Docs](code/html/index.html)**

# User Guide

## What BatLLM Is

BatLLM is a local, AI-mediated, human-vs-human battle game. Human players do not directly move the bots. Instead, each player writes prompts, the configured LLM interprets those prompts, and the returned commands drive the bots inside the arena.

## First Run

Recommended first-run flow:

1. install the Python dependencies
2. install the Ollama CLI if it is not already available on the machine
3. launch BatLLM with `python src/main.py`
4. open `Settings`
5. click `Ollama Config`
6. start Ollama and choose a local model
7. return to the home screen and begin play

If Ollama is missing and the app cannot start it, BatLLM opens an install-guidance flow instead of attempting an automatic install.

## Screen Guide

### Home Screen

The home screen is the main play surface. It contains:

- one prompt history area and one editable prompt area per player
- `Submit`, `Load`, and `Save` buttons for each player
- the game board and live state labels
- navigation to `Settings` and `History`

When a player submits a prompt, BatLLM stores it in the prompt store and marks that bot ready for the next round. Once both bots are ready, the game board runs the next round.

#### `Esc` On The Home Screen

Pressing `Esc` on the home screen runs the exit flow. The exact behavior depends on the current settings:

- if `Confirm on Exit` is enabled, BatLLM asks for confirmation
- if `Prompt to Save on Exit` is enabled, BatLLM offers a filename prompt before exit
- if both are disabled, BatLLM exits immediately

### Settings Screen

The settings screen controls these live values:

- `Total Rounds`
- `Total Turns`
- `Initial Health`
- `Bullet Damage`
- `Shield Size (°)`
- `Step Length`
- `Independent Models`
- `Prompt Augmentation`
- `Confirm on Exit`
- `Prompt to Save on Exit`

Buttons on this screen:

- `Cancel`
- `Set as Defaults`
- `Set Temporarily`
- `Ollama Config`

#### `Esc` On The Settings Screen

Pressing `Esc` on the settings screen behaves like `Cancel` and returns to the home screen.

### History Screen

The history screen shows two synchronized views:

- a compact, per-bot prompt history panel
- the full session history panel from `HistoryManager`

The current implementation uses the explicit `Back` button to return home.

### Ollama Config Screen

The Ollama screen is the main control surface for BatLLM's local model workflow.

It includes:

- an `Ollama Status` section
- an `Output` log
- a `Local Models` section
- a `Remote Models` section
- a `Back to Settings` button

#### Start And Stop Ollama

- `Start Ollama` runs `start_ollama.sh`
- `Stop Ollama` runs `stop_ollama.sh -v`
- `Refresh` reloads status plus both model lists

#### Local Models

Press the local-model selector to:

1. refresh the local list from `/api/tags`
2. open the `Local Models` picker
3. choose a model from the modal list

The picker:

- is modal
- shows the current selection with a darker highlighted row
- renders list text in white
- uses touching rows with no visual gap between models
- closes on `Esc`
- closes if you click outside the popup
- closes if you click `Close`

After choosing a local model:

- `Use Selected` saves the selected model into `llm.model`
- BatLLM then attempts to make that model ready for gameplay
- if BatLLM previously managed a different model itself, it may stop that earlier managed model first

`Delete Selected` asks for confirmation and then removes the selected local Ollama model.

#### Remote Models

Press the remote-model selector to:

1. refresh the remote list from `https://ollama.com/library`
2. open the `Remote Models` picker
3. choose a remote model candidate

`Download Selected` asks for confirmation and then pulls that model into the local Ollama installation.

Remote-model names are not immediately playable. They become local models only after a successful pull.

#### `Esc` On The Ollama Screen

- if a model picker is open, `Esc` closes the picker
- otherwise, `Esc` returns to `Settings`

## Playing A Match

A typical match flow is:

1. each player writes a prompt
2. each player submits the prompt
3. BatLLM starts the round once both bots are ready
4. on each turn, BatLLM sends the appropriate prompt history and game state to the LLM
5. the returned command is executed in the arena
6. the round ends when turn limits are reached or a bot is destroyed

The game state and chat history are recorded centrally by `HistoryManager`.

## Bot Commands

| Command | Meaning |
| --- | --- |
| `C{angle}` | rotate clockwise by `angle` degrees |
| `A{angle}` | rotate anticlockwise by `angle` degrees |
| `M{step}` | move forward by the supplied step value |
| `M` | move forward by the configured default step length |
| `S1` | raise shield |
| `S0` | lower shield |
| `S` | toggle shield |
| `B` | fire one shot if the shield is down |

Any other output is treated as no valid command for that turn.

## Prompt Modes

### Independent Models

Each bot keeps an isolated history. This is controlled by `Independent Models`.

### Shared Context

If `Independent Models` is disabled, both bots share one model history.

### Prompt Augmentation

If `Prompt Augmentation` is enabled, BatLLM prepends structured game-state information to the player's prompt before sending it to the model.

## Safety And Operational Notes

1. BatLLM's Ollama screen operates on the real local Ollama installation, not a private BatLLM-only copy.
2. Deleting a model in BatLLM deletes the local model itself.
3. Downloading a model in BatLLM adds it to the same local model inventory used by other Ollama-based tools on the machine.
4. Starting or stopping Ollama in BatLLM affects the configured local host and port.

## Where To Go Next

- configuration details: [CONFIGURATION.md](CONFIGURATION.md)
- failure cases and setup issues: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- testing and validation: [TESTING.md](TESTING.md)
