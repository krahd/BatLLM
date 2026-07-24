> ![BatLLM logo](./images/logo-small.png) **[Project](../README.md) · [Documentation](README.md) · [User Guide](USER_GUIDE.md) · [FAQ](FAQ.md) · [Contributing](CONTRIBUTING.md) · [Status](../STATUS.md) · [Releases](https://github.com/krahd/BatLLM/releases)**

# User Guide

BatLLM is a two-player battle game mediated by local language models. Each human player writes a prompt for a bot. The model reads that prompt and returns one command at a time; BatLLM executes the command in the arena.

Players do not control the bots directly during ordinary play. The point is to learn how strategy, wording, model choice, prompt augmentation, and conversation history affect what the model actually does.

![BatLLM gameplay demonstration](./screenshots/quick_demo.gif)

## Before playing

Install and launch BatLLM using the instructions in the [project README](../README.md).

For normal play you also need:

- a local Ollama installation;
- at least one model installed in Ollama; and
- enough memory for the model you choose.

BatLLM can open the official Ollama installer and can manage the configured local service from **Settings → Ollama Config**.

> [!CAUTION]
> The Ollama controls affect the real local installation. Starting or stopping the service, downloading a model, deleting a model, or changing the selected model can affect other Ollama-based tools on the same machine.

## Your first game

1. Launch BatLLM.
2. Open **Settings**.
3. Open **Ollama Config**.
4. Start Ollama if it is stopped.
5. Select an installed model with **Local Models**, then press **Use Selected**.
6. Return to the home screen.
7. Each player writes a prompt and presses **Submit**.
8. The round starts after both prompts have been submitted.
9. Watch the actions, then open **History** to inspect the model inputs and outputs.
10. Write revised prompts for the next round.

A useful learning rhythm is: **prompt → observe → inspect → revise**.

## Sessions, games, rounds, and turns

BatLLM uses four nested levels:

- A **session** is one execution of the application.
- A session can contain one or more **games**.
- A game contains one or more **rounds**.
- A round contains a sequence of **turns**.

At the start of each round, both players submit the prompt that will guide their bot throughout that round. During each turn, both bots may execute one command, unless a bot is destroyed before the second action occurs.

The configured round and turn limits are shown and edited in **Settings**.

## Objective and core rules

The objective is to reduce the opposing bot's health to zero while keeping your own bot alive.

- Bots can move, rotate, raise or lower their shields, and fire.
- A bot cannot fire while its shield is raised.
- A shot that reaches the opponent may be blocked by the shield or remove health.
- The game ends immediately when a bot's health reaches zero.
- A round also ends when its configured turn limit is reached.
- If the game has more rounds remaining and both bots are alive, the players can submit new prompts for the next round.

The first bot to act is chosen at the start of a round. That order remains fixed for the round.

## Command language

The model should return exactly one recognised command. Extra prose or malformed output is treated as an invalid action.

| Command | Meaning | Example |
| --- | --- | --- |
| `C<angle>` | rotate clockwise | `C90` |
| `A<angle>` | rotate anticlockwise | `A45` |
| `M` | move forward using the configured default step | `M` |
| `M<distance>` | move forward by a supplied normalised distance | `M0.2` |
| `S1` | raise the shield | `S1` |
| `S0` | lower the shield | `S0` |
| `S` | toggle the shield | `S` |
| `B` | fire, provided the shield is down | `B` |

Angles and distances must be finite numbers with no surrounding text. Commands are case-insensitive after BatLLM strips leading and trailing whitespace, but prompts should still ask for the exact uppercase form to reduce ambiguity.

## Prompting modes

### Prompt augmentation

When **Prompt Augmentation** is enabled, BatLLM prepends structured game-state information to the player's prompt. This gives the model direct information about positions, rotations, health, and shields.

When it is disabled, the model receives the player's text without the structured game-state block.

Prompt augmentation changes the information available to the model. It does not guarantee a valid or strategically useful command.

### Independent and shared contexts

When **Independent Models** is enabled, each bot has a separate conversation history.

When it is disabled, both bots use one shared history. Shared context can expose one player's previous instructions or produce interference between strategies. This is an intentional experimental condition, not a private two-channel mode.

Each new game starts with a fresh model conversation history.

## Main screens

### Home

The home screen contains:

- one editable prompt area for each player;
- prompt-history controls;
- the arena and current bot state;
- **Settings**;
- **History**;
- **Game Analyzer**;
- **Save Session**; and
- the control for starting a new game.

Prompts cannot be replaced while a round is already running. A rejected submission remains in the editor so it can be submitted after the round ends.

Pressing `Esc` follows the configured exit behaviour. BatLLM may ask for confirmation, offer to save the session, or exit immediately depending on the settings.

### Settings

The settings screen controls:

- total rounds;
- turns per round;
- initial health;
- bullet damage;
- shield size;
- default movement step;
- independent or shared model contexts;
- prompt augmentation;
- exit confirmation;
- save-on-exit prompting;
- automatic Ollama startup; and
- automatic Ollama shutdown.

Use **Set Temporarily** to apply values for the current execution without saving them as defaults. Use **Set as Defaults** to write them to the active configuration file.

`Esc` behaves like **Cancel** and returns to the home screen.

### History

The History screen shows compact per-bot histories and the fuller session record. Use it to compare:

- the player's prompt;
- any augmented game state;
- the raw model response;
- the parsed command; and
- the resulting action.

The explicit **Back** button returns to the home screen.

### Game Analyzer

The Game Analyzer is a read-only mode for saved sessions. Open it from the home screen or launch it separately with:

```bash
python run_game_analyzer.py
```

The analyzer can:

- load one saved-session JSON file;
- select a game and round;
- step through turn starts and individual bot actions;
- reconstruct the board from the saved rules and ordered plays;
- show prompts, raw responses, parsed commands, state changes, model metadata, and replay warnings.

The user-facing analyzer supports the current BatLLM session schema v2. Older top-level list exports are rejected rather than replayed approximately.

## Saving sessions

**Save Session** writes an analyzer-compatible JSON file to the configured saved-session folder.

Only completed turns are exported. An active turn or a cancelled zero-play turn is omitted so that unfinished state does not invalidate an otherwise useful session.

Saved rounds include a frozen gameplay-settings snapshot. Saved sessions also include model/runtime metadata. The analyzer therefore uses the rules recorded with the session rather than the current settings file.

Configuration and save locations depend on how BatLLM was launched. See [Installation channels and mutable state](STATE_AND_INSTALLATION.md).

## Ollama Config

The Ollama screen provides:

- installation or reinstallation launch;
- service start and stop controls;
- current service status;
- an output log;
- startup warm-up timeout controls;
- local model selection and deletion; and
- remote model discovery and download.

### Local models

A local model is already installed in Ollama.

1. Open **Local Models**.
2. Choose a model.
3. Press **Use Selected**.

BatLLM saves the model name, attempts to warm it for gameplay, and records it as the last successfully served model when warm-up succeeds.

The local-model timeout controls can save or remove a per-model request-timeout override.

**Delete Selected** removes the model from the real local Ollama installation after confirmation.

### Remote models

A remote model is only a catalogue entry until it has been downloaded.

1. Open **Remote Models**.
2. Choose a model name.
3. Press **Download Selected**.

After a successful download, the model appears in the local model list and can be selected for play.

### Warm-up timeout

The warm-up timeout controls how long BatLLM waits when starting Ollama and preparing a model.

- **Save Warmup** stores the configured value.
- **Use Default** removes the override and returns to the built-in 30-second default.

This startup warm-up timeout is separate from per-request model timeouts.

## Troubleshooting

### The game starts but no actions occur

Check the History screen. The most common cause is a response that does not match the command language exactly.

### Ollama is installed but BatLLM cannot reach it

- confirm that Ollama is running;
- press **Refresh** in **Ollama Config**;
- verify the configured host and port; and
- inspect the Ollama output log.

### The model list is empty

Refresh the Ollama screen and confirm that the configured service is reachable. Remote catalogue access may also require network connectivity.

### A saved session will not open in the analyzer

The analyzer requires the current session-v2 envelope. Legacy top-level list exports are intentionally unsupported.

More detailed developer troubleshooting is in [CONTRIBUTING.md](CONTRIBUTING.md).
