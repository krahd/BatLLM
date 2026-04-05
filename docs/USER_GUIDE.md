> ![BatLLM logo](./images/logo-small.png) **[README](README.md) · [Overview](DOCUMENTATION.md) · [User Guide](USER_GUIDE.md) · [Contributing](CONTRIBUTING.md) · [FAQ](FAQ.md) · [Changelog](CHANGELOG.md) · [Credits](CREDITS.md) · [Releases](https://github.com/krahd/BatLLM/releases)**

# User Guide

BatLLM is a local, AI-mediated, human-vs-human battle game. Two human players write prompts, two model-backed bots interpret those prompts, and the bots act inside the arena. Players do not directly move the bots. The challenge is to guide them through language.

BatLLM is strictly human-vs-human in the current version. There are no NPC bots, autonomous opponents, or single-player campaign modes.

The screen recording below shows the basic flow: players enter prompts, submit them, and trigger a round once both bots are ready.

Prompts can be loaded and saved to disk, the history screen can be used to inspect what each model received and returned, and the Game Analyzer can replay saved sessions later for study.

![BatLLM demo](./screenshots/quick_demo.gif)

## Before You Begin

Recommended first-run flow:

1. install the Python dependencies
2. install the Ollama CLI if it is not already available on the machine, or let BatLLM launch the official installer for you
3. launch BatLLM with `python run_batllm.py`
4. open `Settings`
5. click `Ollama Config`
6. start Ollama and choose a local model
7. return to the home screen and begin play

If Ollama is missing, BatLLM asks whether you want to launch the official install flow. If Ollama is installed but stopped, BatLLM asks whether you want to start it unless `Start Ollama Automatically on BatLLM Launch` is enabled.

The release bundles also include platform-specific launchers:

- Windows: `run-batllm.bat`
- macOS: `run-batllm.command`
- Linux: `run-batllm.sh`

They also include the standalone analyzer launchers:

- Windows: `run-game-analyzer.bat`
- macOS: `run-game-analyzer.command`
- Linux: `run-game-analyzer.sh`

> [!CAUTION]
> BatLLM's Ollama controls operate on your real local Ollama installation. Starting or stopping the service, downloading models, deleting models, or changing the selected model can affect other Ollama-based tools on the same machine.

## Your First Match

If you want the shortest possible route into the game, use this tutorial:

1. Launch BatLLM and open `Settings`.
2. Open `Ollama Config`, start Ollama, and choose a local model.
3. Return to the home screen.
4. Each player writes one prompt for their bot.
5. Each player presses `Submit`.
6. Once both prompts are submitted, BatLLM starts the round automatically.
7. Watch what the bots do, then open `History` if you want to inspect the model inputs and outputs before the next round.

The main rhythm of the game is simple: write a prompt, submit it, watch the outcome, study what happened, and improve the next prompt.

## What You Are Trying To Do

BatLLM is a battle game. Your aim is to outplay the other human player by getting your bot to move, rotate, shield, and fire more effectively than theirs.

Because the bot only acts through the model, success depends on both strategy and prompt-writing. A good plan is not enough if your model misreads it, and a perfectly clear prompt is not enough if the plan behind it is weak.

## Match Structure

The game is easiest to understand in layers:

- a session is one run of the app
- a match is the full game played inside that session
- a match contains one or more rounds
- each round contains several turns
- each turn contains up to two bot actions, one per bot

By convention, BatLLM is built around a 1:1:1 correspondence between human players, bots, and model roles.

## How A Round Works

Before a round begins, both players write a prompt for their bot. Once both prompts have been submitted, the round starts.

During the round:

1. At the start of the round, BatLLM randomly chooses which bot acts first. That order is then used for the turns in that round.
2. The first bot's prompt is sent to the model.
3. The returned command is executed immediately in the arena.
4. If the command is a shot, the bullet's full travel and collision resolution happen as part of that turn.
5. The second bot then acts, unless the round already ended.
6. This repeats until a bot is destroyed or the round reaches its configured turn limit.

## Rules Of Play

The core rules are:

1. A round begins only after both players have submitted prompts.
2. On each turn, both bots may act, unless one is destroyed before the second action happens.
3. A bullet travels until it hits the other bot or leaves the arena.
4. A bullet that hits outside the shield removes health according to `Bullet Damage`.
5. A bot cannot fire while its shield is up.
6. If a bot's health reaches zero, the match ends immediately.
7. If the configured turn limit is reached and no bot has been destroyed, the round ends automatically.
8. If multiple rounds are enabled and both bots are still in play, the next round can begin.

Between rounds, players can adapt. That is a key part of the game: study what the model did in the previous round, then write a better prompt for the next one.

## Bot Commands Reference

The model is expected to return commands in a very strict format. If the output does not match one of the recognised commands below, that turn is treated as no valid action.

| Command | Action | Example |
| --- | --- | --- |
| `C{angle}` | Rotate clockwise by `angle` degrees | `C90` |
| `A{angle}` | Rotate anticlockwise by `angle` degrees | `A45` |
| `M{step}` | Move forward by the supplied step value | `M0.3` |
| `M` | Move forward by the configured default step length | `M` |
| `S1` | Raise shield | `S1` |
| `S0` | Lower shield | `S0` |
| `S` | Toggle shield | `S` |
| `B` | Fire one shot if the shield is down | `B` |

Anything else is ignored as a valid gameplay command.

## Playing Modes

BatLLM supports several ways to play the same core game.

### Standard Prompting

In the basic mode, each player writes a prompt at the beginning of a round and the model acts on that prompt without extra game-state augmentation.

### Prompt Augmentation

If `Prompt Augmentation` is enabled, BatLLM prepends structured game-state information to the player's prompt before sending it to the model.

This usually makes the model better informed, but it does not remove the need for a good prompt. It changes the style of play rather than eliminating prompt skill.

### Independent Models

If `Independent Models` is enabled, each bot keeps its own prompt and response history. The two players are effectively working through separate model contexts.

### Shared Context

If `Independent Models` is disabled, both bots share one model history. This can create interference, leakage between strategies, or unexpected model behaviour, which is part of the challenge.

## Screens And Menus

### Home Screen

The home screen is the main play surface. It contains:

- one prompt history area and one editable prompt area per player
- `Submit`, `Load`, and `Save` buttons for each player
- the game board and live state labels
- `Settings`, `History`, `Game Analyzer`, and `Save Session` controls

This is where most play happens. Write prompts, submit them, and watch the arena.

### `Esc` On The Home Screen

Pressing `Esc` on the home screen runs the exit flow. The exact behaviour depends on the current settings:

- if `Confirm on Exit` is enabled, BatLLM asks for confirmation
- if `Prompt to Save on Exit` is enabled, BatLLM offers a filename prompt before exit
- if both are disabled, BatLLM exits immediately

### Settings Screen

The settings screen controls the main gameplay values:

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
- `Start Ollama Automatically on BatLLM Launch`
- `Stop Ollama Automatically on BatLLM Quit`

Buttons on this screen:

- `Cancel`
- `Set as Defaults`
- `Set Temporarily`
- `Ollama Config`

Use `Set Temporarily` when you want the current session to use those values without changing the saved defaults. Use `Set as Defaults` when you want the changes written back for future runs.

### `Esc` On The Settings Screen

Pressing `Esc` on the settings screen behaves like `Cancel` and returns to the home screen.

### History Screen

The history screen shows two synchronised views:

- a compact, per-bot prompt history panel
- the full session history panel from `HistoryManager`

This is the best place to inspect what each model saw, what it returned, and how your prompt strategy is evolving across rounds.

Use `Save Session` on the home screen to export the current session as a JSON file in `saved_sessions_folder`. Current exports use the BatLLM v2 session format and include a `gameplay_settings_snapshot` for every round so the Game Analyzer can replay the same rules later.

The current implementation uses the explicit `Back` button to return home.

### Game Analyzer

The Game Analyzer is a read-only review mode for saved sessions. You can open it either from the home screen or through the standalone launcher:

```bash
python run_game_analyzer.py
```

The analyzer lets you:

- load a saved session JSON
- choose a game and round inside that session
- move backward and forward across turn starts and individual plays
- replay the board using the saved prompts, ordered plays, and that round's frozen gameplay settings snapshot
- inspect prompts, raw model responses, parsed commands, state diffs, round settings, and mismatch warnings

Legacy saved sessions that predate the v2 schema are not replay-supported in the analyzer. Save a new session from the current app if you want to study it there.

### Ollama Config Screen

The Ollama screen is the main control surface for BatLLM's local model workflow.

It includes:

- an `Ollama Status` section
- an `Output` log
- a `Local Models` section
- a `Remote Models` section
- a `Back to Settings` button

### Start And Stop Ollama

- `Install Ollama` launches the official install or reinstall flow after confirmation
- `Start Ollama` runs BatLLM's cross-platform Ollama helper
- `Stop Ollama` runs the same helper in stop mode
- `Refresh` reloads status plus both model lists

### Local Models

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
- successful warm-up also updates `llm.last_served_model`
- if BatLLM previously managed a different model itself, it may stop that earlier managed model first

`Delete Selected` asks for confirmation and then removes the selected local Ollama model.

### Remote Models

Press the remote-model selector to:

1. refresh the remote list from `https://ollama.com/library`
2. open the `Remote Models` picker
3. choose a remote model candidate

`Download Selected` asks for confirmation and then pulls that model into the local Ollama installation.

Remote-model names are not immediately playable. They become local models only after a successful pull.

### `Esc` On The Ollama Screen

- if a model picker is open, `Esc` closes the picker
- otherwise, `Esc` returns to `Settings`

## Ollama And Model Management

BatLLM uses Ollama in two ways:

- the Python `ollama` package for gameplay chat requests
- the `ollama` CLI and local HTTP endpoints for model and service management

If you already manage Ollama elsewhere, you can keep doing that. The in-app Ollama screen is recommended, but it is not the only possible workflow.

## Safety Notes

> [!WARNING]
> BatLLM's Ollama screen operates on the real local Ollama installation, not a private BatLLM-only copy.

1. Deleting a model in BatLLM deletes the local model itself.
2. Downloading a model in BatLLM adds it to the same local model inventory used by other Ollama-based tools on the machine.
3. Starting or stopping Ollama in BatLLM affects the configured local host and port.

## Final Advice

Treat BatLLM like a game of strategy played through imperfect intermediaries. Short prompts, overcomplicated prompts, and beautifully reasoned prompts can all fail if the model interprets them badly. Experiment, inspect the history, and refine.

## Where To Go Next

- project overview and entry point: [README.md](README.md)
- recurring non-trivial questions for both players and contributors: [FAQ.md](FAQ.md)
- contributor and developer material: [CONTRIBUTING.md](CONTRIBUTING.md)
