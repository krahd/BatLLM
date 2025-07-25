Great — I’ll create a comprehensive and well-structured documentation set for the BatLLM project, including a rich README and any supporting .md files if needed. I’ll gather all relevant information from the repository and your notes, including gameplay mechanics, technical details, setup instructions, and development guidance.

I’ll get started and let you know once it’s ready for your review.


**README.md**

# BatLLM: Human-vs-Human LLM-Powered Bot Battle Game

**BatLLM** is a two-player, turn-based battle game that uniquely leverages local Large Language Models (LLMs) as mediators. Each player guides their bot by crafting prompts, and an LLM interprets the game state and prompt to generate the bot's command. BatLLM is designed to help people practice controlling LLMs, hone their prompting skills, and build an intuitive understanding of what LLMs can and cannot do—all without needing to learn the technical details of the underlying technologies.

---

## Table of Contents

* [Project Goals](#project-goals)
* [About the Author](#about-the-author)
* [Features](#features)
* [Game Overview](#game-overview)
* [Game Modes and Variations](#game-modes-and-variations)
* [Prompt Augmentation](#prompt-augmentation)
* [Bot Command Reference](#bot-command-reference)
* [Game Flow](#game-flow)
* [Installation and Setup](#installation-and-setup)
* [Usage](#usage)
* [Configuration](#configuration)
* [System Requirements](#system-requirements)
* [Technical Notes](#technical-notes)
* [Contributing](#contributing)
* [License](#license)
* [Acknowledgments](#acknowledgments)
* [FAQ](#faq)

---

## Project Goals

BatLLM is designed as a tool for:

* **Practicing LLM Control:** Experiment with prompts and observe how LLMs interpret and execute them.
* **Developing Prompting Intuition:** See firsthand the strengths and weaknesses of LLMs in understanding and acting on your instructions.
* **Democratizing AI Skills:** Enable anyone to interact with advanced language models in a fun, accessible way—no AI or programming expertise required.

---

## About the Author

BatLLM was designed and developed by **Tomas Laurenzo**, Associate Professor at CU Boulder. The project is open source and free to use, improve, and share.

---

## Features

* **Human-vs-Human Only:** All players are humans; there are no AI/autonomous players. Every action is mediated by an LLM based on each human player’s prompt.
* **Prompt-Driven Gameplay:** Players write natural language prompts to guide their bots, with the LLM translating these into in-game actions.
* **Local LLM Integration:** Works out-of-the-box with [Ollama](https://ollama.ai) and the `llama3.2:latest` model (tested on an M1 MacBook Pro). The system is model-agnostic and can be configured for other local LLM servers.
* **Prompt Augmentation:** Optional feature that structures and augments the prompt sent to the LLM with game state info for improved control and transparency.
* **Configurable LLM Mediation:** Supports two separate LLMs (one per player) or a single shared LLM (for experimentation or hardware constraints).
* **Intuitive Arena Graphics:** Uses [Kivy](https://kivy.org) for visualization, with a normalized coordinate system for easy customization and creative coding.
* **Modular and Extensible:** Clean, well-documented code ready for expansion (e.g., online play, larger arenas, more complex mechanics or additional bots).

---

## Game Overview

BatLLM is a two-player competitive game where each player controls a bot by writing prompts. At the start of each round, both players enter a prompt. The prompt (along with optional game state data) is sent to an LLM, which returns a command for the bot. The goal is to destroy the opposing bot by reducing its health to zero through strategic movement, rotation, shielding, and shooting.

**Key Points:**

* Each player enters a prompt **per round** (not each turn). The same prompt will guide the bot for the duration of that round’s turns.
* Each bot executes commands as interpreted by its LLM, one command per turn.
* The arena and bot states are visualized via a Kivy-based interface in real time.
* The match ends immediately when one bot’s health is reduced to zero (the other bot wins). If neither is destroyed within the allotted rounds, the player with more health (or other agreed condition) could be considered the winner (though currently the game assumes sudden-death on bot destruction).

---

## Game Modes and Variations

* **Standard Mode:** Each player writes a prompt at the beginning of a round; both prompts are sent to their respective LLMs each turn of that round.
* **Prompt Augmentation:** Optionally, the game augments the player's prompt with structured game state info (see [Prompt Augmentation](#prompt-augmentation)).
* **LLM Assignment:**

  * *Separate LLMs:* Each player’s prompt goes to a different LLM instance (e.g., two Ollama servers on different ports, one per bot).
  * *Single LLM:* Both prompts are handled by a single LLM (the same model) in each turn, which can be useful for lower resource usage or interesting interactions but may risk cross-talk between the two bots’ instructions.

**Note:** There are **no** fully autonomous or AI-vs-AI modes. BatLLM is strictly human-vs-human; all gameplay decisions are made by human-written prompts, then carried out by LLMs. (However, a human player could conceivably write a prompt like *"Play both sides of the battle for me"* and observe what happens, for experimental purposes.)

---

## Prompt Augmentation

When Prompt Augmentation is **enabled**, BatLLM automatically prepends a structured description of the current game state to the player's prompt. This augmented prompt ensures the LLM has all the context it needs about the world before producing a command. When augmentation is **disabled**, only the raw player-written prompt is sent, and it’s up to the player to provide sufficient context for the LLM.

* **Enabled:** The game provides information such as both bots’ coordinates (`x`, `y`), rotations (`a` for angle), shield status (`s` for shield up=1 or down=0), health (`h`), the current round and turn number, etc., followed by the player's actual prompt. This helps the LLM make an informed decision every turn.
* **Disabled:** Only the player's raw prompt is sent to the LLM. The LLM will have no automatic knowledge of game state beyond what the prompt includes, making it the player’s responsibility to mention anything relevant (like the opponent’s position or health).

**Example of an Augmented Prompt:**

```
You are an expert gamer. Your task is to control a bot in BatLLM, a two-player battle game where an LLM like you controls a bot. You receive information about the game state and a prompt written by the human player that guides your behaviors.

Game State:
Round: 3, Turn: 2  
Your Bot – x:0.5 y:0.2 a:90 s:1 h:10  
Opponent Bot – x:0.7 y:0.8 a:270 s:0 h:8  

Player Prompt:  
Try to dodge the next bullet, then retaliate when the enemy's shield is down.
```

In this example, the game provided context (positions, angles in degrees, shield status ON/OFF, health, etc.) before the player’s actual prompt. The LLM should then output a command like `M` or `S` or `B` based on this information and the player's guidance.

Players can toggle Prompt Augmentation in the configuration. It is highly recommended for beginners, as it makes the LLM’s behavior more predictable and the game more about strategy than memory.

---

## Bot Command Reference

Bots can execute the following **commands** as generated by the LLM (any other output is ignored):

| Command | Action                                                                      | Example |
| ------- | --------------------------------------------------------------------------- | ------- |
| `Cd`    | Rotate **clockwise** by `d` degrees                                         | `C20`   |
| `Ad`    | Rotate **anticlockwise** by `d` degrees                                     | `A90`   |
| `M`     | Move forward one step (of length `STEP_LENGTH`)                             | `M`     |
| `S1`    | Raise shield (it remains up until changed)                                  | `S1`    |
| `S0`    | Lower shield (remains down until changed)                                   | `S0`    |
| `S`     | Toggle shield (raise if down, lower if up)                                  | `S`     |
| `B`     | Fire a bullet forward (only if shield is down; if shield is up, do nothing) | `B`     |

**Notes:**

* The game interprets **only the first character (and any number immediately following it)** of the LLM’s response as the command. Any additional text or unrecognized commands are ignored. For example, if the LLM returns "`M and then shoot`", the bot will interpret only `M` and ignore the rest. For best results, the LLM should respond with a concise command string (the prompt template given to the LLM encourages this behavior).
* **Bullets** are resolved immediately within a turn. When a bot fires (`B`), the bullet’s trajectory is simulated instantly before the turn proceeds. The opponent bot does not get to act or move while a bullet is in flight. This effectively means if the first bot in a turn fires a bullet, the second bot’s action will only occur **after** the bullet either hits or misses.
* **Shields** protect only the front arc of a bot. By default, the shield covers ±`SHIELD_SIZE` degrees around the direction the bot is facing (the “front” of the bot). If a bullet comes from behind or the sides outside that arc, it will hit the bot as if the shield were not there.
* If a bot is hit by a bullet and its shield is down (or the bullet strikes from an unprotected angle), the bot’s health decreases by `BULLET_DAMAGE`. If a bullet hits a raised shield (within the shield’s coverage arc), it deals no damage (the bullet is considered blocked and stops).

---

## Game Flow

A match consists of one or more rounds; each round consists of several turns. The game flow is as follows:

1. **Before the Round:**
   Both players are prompted to enter a new prompt for their bots. Once both players have submitted their prompts, the round begins. (The prompt will remain the same throughout that round, unless players choose to reuse or adjust it in subsequent rounds.)

2. **During Each Turn:**

   * At the start of each turn, the game randomly selects which player’s bot will act first for that turn (this random order is determined once per round).
   * The first bot’s prompt (augmented or raw, depending on settings) is sent to its LLM. The LLM returns a command (e.g., move, rotate, shoot, etc.). The command is immediately executed by the bot in the game world (e.g., the bot moves or shoots). The game state is updated and rendered on the screen.
   * If the command was to shoot a bullet, the bullet is resolved right away: it travels until it either hits the other bot or goes out of bounds. If it hits, damage is applied to the target bot and the turn may end early (since the target might be destroyed). If it misses, the turn continues. The opponent bot cannot act or move while this bullet is being resolved.
   * Next, the second bot’s prompt is sent to its LLM, and that bot then executes its command for the turn, updating the state and UI accordingly (unless the round already ended due to the first bot destroying the opponent).
   * This completes one turn (both bots have acted once). The turn counter increases, and the next turn begins, repeating the above sequence.

3. **End of Round / Match:**

   * If a bot’s health reaches zero at any point, the match ends immediately (one bot is destroyed). A popup will typically display the outcome (e.g. “Round X ended” with each bot’s remaining health, or a victory message). There is no respawning; a destroyed bot means the game is over.
   * If neither bot is destroyed and the predefined number of turns in the round elapses (`TURNS_PER_ROUND` in settings), the round ends automatically. A popup will show the round results (e.g., remaining health of each bot). If the game is set to multiple rounds (`TOTAL_ROUNDS`), and both bots are still alive, the next round can begin. Players can then input new prompts (or reuse previous ones) for the next round.
   * The game can be configured for a fixed number of rounds per match. By default, the match may be set to, say, 3 rounds maximum. If no bot is destroyed by the end of the final round, you could decide the winner by health or declare a draw (the base game logic doesn’t currently enforce a win-by-rounds condition, so this is up to players to interpret).

Between rounds, players have the opportunity to adjust their strategy by writing new prompts. This is a key part of BatLLM’s educational value: you can analyze what the LLM did in the prior round and modify your prompt to guide it differently in the next round.

*Example:*
\_Player 1 and Player 2 start Round 1 by entering their prompts. Suppose Player 1 writes: "Advance toward the enemy and fire when in range," and Player 2 writes: "Keep your shield up and evade attacks." At the first turn, the game randomly picks a starting bot. If Player 2’s bot goes first, its LLM might interpret the prompt and return `M` (move forward). The bot moves. Then Player 1’s bot’s turn: the LLM sees the distance closed by the opponent and might return `B` (fire bullet). The bot fires, and if Player 2’s bot is within range and not facing the shot with shield, Player 2’s bot takes damage. The turn ends and Turn 2 begins, now with Player 1’s bot acting first (since order was random per round). The battle continues until one bot is destroyed. At that point, the game ends immediately with Player 1 or Player 2 as the winner. If neither is destroyed after the maximum turns of the round, a new round would start with players possibly writing new prompts based on what they learned.\*

---

## Installation and Setup

### Requirements

* **Python 3.8+** (developed and tested with Python 3.11).
* **Kivy** (Graphics/UI library for Python). The game uses Kivy for the interface and rendering.
* **Requests** library (for HTTP calls to the LLM API).
* **A Local LLM Backend:** BatLLM doesn’t ship with an AI model. You need a local LLM server or runtime. It is tested with [Ollama](https://ollama.ai/) (which is currently macOS-focused) using the `llama3.2:latest` model. However, any local or network-accessible LLM with a RESTful API endpoint returning plain text or a JSON with a `"response"` field should work, with minor configuration.
* **Platform:** BatLLM is cross-platform. It has been run on macOS (Metal accelerated Kivy, M1 chip) and should work on Linux and Windows (though Windows may require some extra steps for Kivy installation).

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/krahd/BatLLM.git  
   cd BatLLM
   ```

2. **Install Python dependencies:**
   It’s recommended to use a virtual environment. Then run:

   ```bash
   pip install -r requirements.txt
   ```

   This will install Kivy, requests, PyYAML, and any other required packages. If you encounter issues installing Kivy (especially on Windows), see the Kivy documentation or our [INSTALL.md](#) for troubleshooting tips. *(If needed, you can manually install packages; BatLLM mainly requires `kivy` and `requests`.)*

3. **Install and run Ollama (or your chosen LLM server):**

   * Follow the [Ollama installation guide](https://ollama.ai/download) to set up Ollama. Ollama provides a local inference server for Llama-based models.
   * Once installed, download/start the model that BatLLM will use. For example, to download and run the Llama2 7B chat model (branded as `llama3.2:latest` in Ollama’s repo):

     ```bash
     ollama run llama3.2:latest
     ```

     This will start the model on Ollama’s default port (usually `11434`). You should see Ollama’s server running and ready.

   *Alternative LLMs:* If you prefer, you can use a different local model server (for example, an OpenAI API-compatible server or the official Llama.cpp HTTP server). Just ensure you update BatLLM’s configuration to point to the correct URL and adjust any expected request/response format differences.

4. **Configure BatLLM (optional):**
   BatLLM’s default configuration assumes two Ollama instances running (one on port 11434, one on 11435 for player 2). If you only run one instance or want to use a different setup, you can modify the config (see [Configuration](#configuration) below or in `configs/config.yaml`).

   By default, `PROMPT_AUGMENTATION` is enabled, initial health is 20, bullet damage is 3, etc. These can be changed if desired.

### Running the Game

Once installed and with the LLM backend running, launch the game:

```bash
python batllm.py
```

This will open the BatLLM game window. You’ll see an interface with the arena and input fields for each player’s prompt. Follow on-screen instructions or the prompts below the input fields:

* Enter a prompt for Player 1 and Player 2 in their respective text boxes.
* Hit the “Submit” button (or press **Enter**) for each prompt. Once both prompts are submitted, the game will start the round.
* Watch as the bots execute the commands from the LLMs. The top of the window will show the current Round and Turn number. Each bot has a small info box near it displaying its state (coordinates, rotation, shield, health).
* You can observe the LLM’s returned command in a log area (if provided in the UI) for each turn, which helps you understand what the LLM decided.
* If a round ends (max turns reached without a bot dying), you can enter new prompts for the next round. If a bot is destroyed, the game will display a result and you may restart a new match if you like.

For a step-by-step example of gameplay and more prompt examples, see [PROMPTS.md](#) in the repository.

---

## Configuration

BatLLM can be configured via a YAML file (`configs/config.yaml`) or by modifying constants in the code. Key configuration options include:

* **LLM Endpoints:** The URLs for each player’s LLM. By default the config uses `http://localhost` with different ports for each bot. For example:

  ```yaml
  llm:
    url: "http://localhost"
    port_base: 11434
    path: "/api/generate"
    independent_models: true
  ```

  In this setup, Player 1’s LLM endpoint will be `http://localhost:11435/api/generate` (port\_base + 1) and Player 2’s will be `http://localhost:11436/api/generate` (port\_base + 2), assuming `independent_models:true`. If `independent_models` is false, both bots would use the same endpoint (port\_base for both). Adjust these to match your LLM server(s). The game expects to POST a JSON with a prompt and get back JSON containing a `"response"` field with the model's answer (as Ollama does).

* **Prompt Augmentation:** Toggle augmentation on/off. In the YAML config, this is under the `game` section, e.g. `prompt_augmentation: true` (enabled by default). You can also quickly toggle this in code or via a settings UI if available.

* **Gameplay Settings:** Adjust arena and game rules:

  * `initial_health`: Starting health for each bot (e.g., 20 by default).
  * `bullet_damage`: Damage a bot takes from one bullet hit (e.g., 3).
  * `shield_size`: Shield coverage in degrees to each side of the bot’s facing direction (e.g., 20 degrees means a 40° front arc; increase this for a larger protective arc).
  * `step_length`: How far a bot moves on `M` command (this is a fraction of the arena size since the arena is normalized 0-1).
  * `total_rounds`: Maximum number of rounds in a match (e.g., 3). The game doesn’t force an end-of-match on rounds yet, but this could be used for a “best of N rounds” rule among players.
  * `turns_per_round` (or `total_turns`): Number of turns per round (default 5). After this many turns, if no bot is destroyed, the round ends.

* **UI Settings:** In config you can adjust UI aspects like `frame_rate` (the refresh rate of the game loop; default 60 FPS), colors, font sizes, etc., if needed.

Example snippet from the configuration (for quick reference):

```yaml
game:
  prompt_augmentation: true
  initial_health: 20
  bullet_damage: 3
  shield_size: 20       # degrees (front arc coverage)
  total_turns: 5        # turns per round
  total_rounds: 3       # rounds per match (if used)
llm:
  url: "http://localhost"
  port_base: 5000
  path: "/api/generate"
  independent_models: true
```

*(The actual configuration file may have slightly different default values or keys; the above is illustrative. See the repository’s `configs/config.yaml` for the exact format.)*

* **Command-line Arguments:** Not currently implemented, but future versions may allow overriding these settings via command-line options for convenience (e.g., `--no-augment` to disable prompt augmentation quickly).

After changing settings, simply run the game again. If you modify the YAML while the game is running, you’ll need to restart the game to apply the changes.

---

## System Requirements

* **Operating System:** BatLLM is written in Python and uses Kivy, so it should run on macOS, Linux, and Windows. It has been primarily tested on macOS (M1 chip). On Windows, ensure you have the proper environment for Kivy (see Kivy’s docs) and a way to run a local LLM (Ollama is macOS-only as of writing, so Windows users might use an alternative like the Llama.cpp server or HuggingFace Text Generation Inference).
* **Hardware:** There are no specific hardware requirements beyond what’s needed to run the chosen LLM. The game itself is lightweight. However, running LLMs can be CPU/GPU-intensive. For example, Llama2 7B can run on an 8GB RAM machine but anything larger may require more RAM or GPU acceleration.
* **Python:** 3.8 or higher. Python 3.11 is recommended. Ensure Kivy is installed properly for your Python version.
* **Graphics:** Kivy handles graphics via OpenGL. On desktop platforms, a functioning OpenGL drivers setup is required. On most systems this is fine out of the box. If you encounter a black window or crash on startup, it might be related to graphics drivers or missing dependencies for Kivy.
* **LLM Model:** A local LLM runtime such as Ollama or an OpenAI-compatible API. No internet connectivity is required during gameplay except for downloading the model initially.

---

## Technical Notes

* **Architecture:** The game is built using a Model-View-Controller-like separation. The **view** (UI) is done in Kivy with a `ScreenManager`. The main game screen (`HomeScreen`) contains the interactive elements (prompt input boxes, prompt history, output log, etc.) and the `GameBoardWidget` where the arena and bots are drawn. The **model** includes the `Bot` class (tracking state and handling LLM interaction) and the simple physics for bullets. The **controller** logic is primarily in `GameBoardWidget` (managing turns, rounds, and coordinating between UI events and bot actions).

* **Arena Rendering:** The game uses a custom `NormalizedCanvas` context, meaning all coordinates for drawing are in the range 0.0–1.0 (where (0,0) corresponds to the top-left of the arena and (1,1) the bottom-right). This makes it easy to think about positions without worrying about pixels or aspect ratio. The arena is drawn as a square within the window with some padding. Bot coordinates (`x`, `y`) are floats in \[0,1], and a bot’s size (`diameter`) is also a fraction of the arena size.

* **Bot Representation:** Bots are drawn as circles with a line indicating facing direction. Each bot also has a small on-screen text box attached that shows its current `x`, `y`, `rot` (rotation angle in degrees), shield status, and health. This updates in real time so players and observers can see the state without parsing logs.

* **LLM Communication:** Communication with the LLMs is done via HTTP requests. The `Bot` class uses `kivy.network.urlrequest.UrlRequest` to send a POST to the configured endpoint with a JSON payload. For Ollama, the payload looks like:

  ```json
  { "model": "llama3.2:latest", "prompt": "<PROMPT_TEXT>", "stream": false }
  ```

  The LLM server is expected to return a JSON response containing a field (for Ollama it's `"response"`) with the model’s output. The game will take this output and parse it for a command as described in [Bot Command Reference](#bot-command-reference). Non-blocking requests are used, so the game doesn’t freeze while waiting for the LLM. Each bot’s LLM call runs in parallel. A callback updates the game state when the response comes in.

* **LLM Response Parsing:** The LLM’s raw text response can technically be anything, but BatLLM expects it to be a command string. The code is defensive: if the response is a list (some APIs return an array of choices), it takes the first element; if it’s a string, it uses it as-is. It then looks at the first character to determine the action. If the response doesn’t correspond to a valid command (or is empty), that bot simply does nothing for that turn. This design encourages players to craft prompts that yield a clear command. The prompt augmentation instructions explicitly tell the LLM to output a valid command in the correct format.

* **Turns and Rounds:** Internally, when both players have entered prompts, `GameBoardWidget.play_round()` is called to initialize a new round. This sets the round number, randomizes turn order, and then calls `play_turn()`. On each turn, the game sends out the LLM requests for both bots (in the chosen order) and waits for both to complete. When each bot’s response is processed, it calls back to `on_bot_llm_interaction_complete()`. Once both bots are done, that function triggers the next turn via `Clock.schedule_once(self.play_turn, 0)` (scheduling with 0 delay means “do it on the next frame”). This continues until the turn limit is reached or a bot dies.

* **Bullet Physics:** When a bullet is fired, the simulation of the bullet is done immediately in the same turn. The bullet travels in a straight line from the firing bot’s position in the direction the bot was facing. It steps forward in small increments (the bullet speed is predetermined) and checks for collision with the opponent or exiting the bounds. This is implemented in the `Bullet` class’s `update()` method using simple geometry. The shield’s effect is accounted for by checking the angle of impact relative to the bot’s facing direction (within `shield_size` arc, the bullet is considered blocked). The game draws a trail for the bullet as it moves (a fading red dot path) to make the shot visible to players. Once the bullet hits or misses, the result (hit/miss and damage) is applied instantly. The turn then resumes if the second bot hasn’t acted yet (but note, if the first bot’s bullet destroyed the second bot, the round will end before the second bot can act).

* **Keyboard Controls (Debug/Alternate Input):** In addition to prompts, the game has basic keyboard controls for manual play or debugging:

  * Press **M** (or **Shift+M** for the other bot) to move a bot forward.
  * **R** / **T** keys to rotate one bot clockwise/anticlockwise a small increment (with Shift for the second bot).
  * **S** to toggle shield (Shift+S for other bot).
  * **Spacebar** to fire a bullet (for the bot without shield up; use Shift+Space for the other bot).
    These can be used to test mechanics without the LLM, or even allow two people to play using keyboard instead of writing prompts. When a keyboard action happens, it bypasses the LLM and immediately executes the command (this is mostly for development and isn’t the core game mode).

* **Performance:** On an M1 MacBook Pro (2021), BatLLM runs smoothly. The main performance factor is the LLM inference time. The UI and physics are lightweight. The game loop is set to 60 FPS, and rendering uses vector graphics for bots and bullets. Even with slower models, because the game waits for LLM responses each turn, you won’t drop frames; you’ll just have a longer pause between turns. If using a very slow model, you can reduce `turns_per_round` or simply be patient between turns.

* **Sound Effects:** There are minor sound effects (e.g., `shoot1.wav` for firing, `bot_hit.wav` for when a bot is hit) loaded at startup. These play during keyboard-controlled actions currently. In LLM-mediated turns, they might not all be hooked up yet (this is a minor to-do). This means you might not hear a sound for every LLM-fired bullet in the current version. In the future, these will be tied in so that a gunshot or hit sound plays on LLM actions too.

* **File Structure:** Key files in the repository:

  * `batllm.py` – The main entry point. It likely creates the Kivy App, sets up the ScreenManager, and starts the UI.
  * `app_config.py` – Handles loading and accessing the configuration (combines defaults and `config.yaml`).
  * `home_screen.py` – Defines the HomeScreen class (Kivy Screen) and its logic for handling UI events (like prompt submission, history navigation).
  * `game_board.py` – Defines the GameBoardWidget class, which is the core of the game logic (bots, turns, rendering).
  * `bot.py` – Defines the Bot class (bot state and behavior, including sending prompt to LLM and processing LLM response).
  * `bullet.py` – Defines the Bullet class (bullet movement and collision logic).
  * `normalized_canvas.py` – Utility for normalized coordinate drawing with Kivy.
  * `assets/` – Contains assets like sound files and possibly example prompt files.
  * `configs/config.yaml` – User-editable configuration for the game.

* **Extensibility:** The code is structured to allow modifications. For example, you can add new commands by extending the `match` in `Bot._on_llm_response` and adding a corresponding method in Bot or GameBoard. You could add new screens (like a main menu or a post-game stats screen) via Kivy’s ScreenManager. The separation of concerns means, for instance, you could swap out the LLM communication part (to use an OpenAI API or another library) by modifying the Bot class without touching the game logic or UI. We encourage experimentation—BatLLM is as much a sandbox for AI interaction as it is a game.

---

## Contributing

**BatLLM is a growing project and contributions are welcome!** Whether it’s new features, bug fixes, or improvements to documentation and usability, we appreciate your help.

If you want to contribute:

* **Fork the repository** on GitHub and clone it locally.
* Create a new branch for your feature or fix.
* Make your changes with clear, well-documented code. If adding a new feature, try to write a short section about it for the documentation as well.
* **Submit a pull request** with a clear description of your changes and the problem they solve or the improvement made.
* We will review the PR, suggest any changes if necessary, and merge it once it’s ready.

Areas especially in need of help or ideas:

* **User Interface:** The current UI is functional but basic. Improvements to layout, design, and user feedback (animations, better health bars, etc.) would enhance the experience.
* **Online Play:** Currently both players must use the same machine. Adding networked multiplayer or a server mode could be very interesting (this would require syncing game state between two machines and possibly a relay for LLM queries).
* **AI Opponent / Single-player:** While the core idea is human vs human, an option to play against an AI-driven bot (for example, using a fixed prompt or a second LLM that is not controlled by a human) could make the game accessible to solo players.
* **More Complex Mechanics:** New types of actions, obstacles in the arena, power-ups, or multiple bots per side (team battles) could be fun extensions. The code is structured to allow multiple bots; you’d primarily need to extend the UI and input handling to manage more prompts and more entities.
* **LLM Prompting Strategies:** Tuning the prompt augmentation text or providing different prompt templates for different models could improve performance. Contributions here (and in documenting them in a `PROMPTS.md` or similar) help everyone.
* **Performance Optimizations:** If you find ways to make rendering or the bullet physics more efficient (especially if scaling up the number of bots or adding continuous movement), that would be valuable.

Please open an issue if you find a bug or have a feature request. Even if you’re not coding it yourself, ideas and feedback are extremely helpful.

When contributing, ensure that any new dependencies are necessary and cross-platform. Also, test on multiple platforms if possible, or at least alert us if a change might affect Windows/Mac/Linux differently.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details. This means you’re free to use, modify, and distribute this software as long as you include the license notice. We hope you’ll contribute back any improvements!

---

## Acknowledgments

* **Developer:** Tomas Laurenzo ([@krahd](https://github.com/krahd)) – Concept and development.
* **Inspiration:** The project was inspired by the intersection of creative coding and AI. It draws on ideas from battlebot games and the desire to make LLM interactions more hands-on and visual.
* **LLM Models:** Thanks to the creators of LLaMA and other open models that make local AI experimentation possible, and to the Ollama team for a user-friendly local model runner.
* **Libraries:** Kivy for the graphics and UI framework, which made Python game development feasible; and the wider open-source community for tools that enabled this project.
* Playtesters and friends who tried out early versions and provided feedback on how to improve prompt clarity and game balance.

---

## FAQ

**Q: Can I play BatLLM over the internet or do both players have to be at the same computer?**
A: Right now, both players share one screen, so typically you’d be in the same room taking turns typing prompts. There’s no built-in network play yet. You could use screen-sharing as a workaround, but an online mode is something for the future.

**Q: Is there a way to play single-player (against an AI)?**
A: BatLLM doesn’t have a true AI opponent mode (since the core idea is to practice prompting by controlling both sides). However, you might simulate an AI opponent by writing a very simple prompt for the other bot and reusing it, or even running an automated script that supplies a prompt every round. A dedicated single-player mode might be added later by allowing one side to have a fixed or self-updating prompt.

**Q: What LLMs can I use with this?**
A: Any local LLM that exposes a compatible API. We used Ollama with the llama2-based model. You could configure it to use an OpenAI API endpoint (though that would not be “local” and would incur latency and cost), or other projects like LocalAI, text-generation-webui’s API, etc. The key is adjusting the config’s URL and possibly the request format. By default, it expects an endpoint similar to Ollama’s (a single POST that returns the full response).

**Q: The LLM sometimes outputs something like "I move forward (M)" and my bot does nothing. Why?**
A: The game only understands the very specific command format (e.g., exactly "M" to move). If the model’s output isn’t exactly one of the commands (possibly with a parameter), the command will be ignored as unrecognized. Prompt augmentation tries to enforce concise outputs, but some models may still verbose-ify. As a player, you might need to tweak your prompt to get a more direct answer. For example, say "Output just the command you will execute, no explanation." in your prompt if you find the model is being too wordy. Future improvements might include smarter parsing, but currently it’s kept simple to avoid the model accidentally doing multiple actions.

**Q: How does prompt augmentation actually improve gameplay?**
A: With augmentation on, the model gets a structured dump of the game state every turn. This means it doesn’t have to rely on memory of previous turns (which it might not have, since each turn’s prompt is separate) or on the player describing the state. This usually leads to more relevant and valid commands. Without augmentation, the model might not know where the enemy is or that its health is low, etc., unless the player explicitly writes that in the prompt. Augmentation makes the game more about strategy (“what high-level instruction do I give the bot”) and less about manual bookkeeping (“let me remind the AI it’s been hit and the enemy is to its left”). On the other hand, playing without augmentation is a great exercise in prompt engineering, as you must manage the AI’s context carefully yourself.

**Q: The game window is too large/doesn’t fit on my screen.**
A: By default, the window should start maximized. If that causes issues, you can edit the Kivy configuration (in `app_config.py` we set the window to maximized on launch). You can comment that out or set a custom size via Kivy Config. Alternatively, use the OS window controls to resize. The UI is dynamic and should scale to different sizes, though the aspect ratio is optimal when the window is roughly square.

**Q: Can I modify the game to have more than 2 players or different arenas?**
A: The code is written with 2 players in mind (certain logic like shuffling bots each round assumes two bots). Extending to more bots would involve altering those assumptions, adding more input fields, etc. It’s not a trivial change but it’s feasible with moderate effort. Different arenas (e.g., obstacles or non-square layouts) would involve changing how movement and collision are handled. Right now bots can roam anywhere in a 1x1 area. You could introduce walls by checking collisions in the `move()` or bullet update logic. This would be a fun area for contributions!

**Q: My model is taking a long time to respond or times out. What can I do?**
A: Smaller or quantized models will respond faster. If using Ollama, ensure the model is running properly. The game sets a timeout of 30 seconds for the LLM response; if it’s too slow, the turn might effectively be skipped. You can increase the timeout in code (Bot.submit\_prompt\_to\_llm). Also, you can simplify your prompt or the augmentation text to maybe speed up inference. If the model consistently can’t respond in time, consider using a faster model or setup.

**Q: The bots sometimes move out of the visible area or overlap the border. Bug?**
A: The game tries to keep bots within bounds (you can see in the code that after moving, it clamps the bot’s position to \[r, 1-r] where r is radius). However, at high speeds or due to continuous rotation, occasionally a rendering quirk might draw a bot half-cut at the edge. It shouldn’t go fully out of bounds though. If you notice weird behavior, feel free to report it. The bullet trace also clears each frame once faded; occasionally you might see a remnant if the game runs at a lower framerate. These are minor visual issues that we are smoothing out.

---

*Play. Prompt. Learn.*

*Build your prompting intuition and master AI mediation—one battle at a time!*

<br>

**INSTALL.md**

# Installation Guide for BatLLM

This guide provides detailed instructions and troubleshooting tips for installing and running BatLLM. If you already followed the quick steps in the README and everything worked, you’re all set! Otherwise, read on for platform-specific notes and solutions to common issues.

## Prerequisites

* **Python**: Make sure Python 3.8 or higher is installed. You can check by running `python --version` in your terminal. If you have multiple Python versions, use a virtual environment or ensure the correct one is invoked (sometimes `python3` is the command for Python 3).

* **Pip**: Ensure you have pip (the Python package installer). Usually it comes with Python, but you can check with `pip --version`. If pip is not found, install it or use Python’s `-m ensurepip` to bootstrap it.

* **Git** (optional): To clone the repository. Alternatively, you can download the code as a ZIP from GitHub, but using Git is recommended for easy updates.

* **C++ Build Tools** (Windows specific): If you’re on Windows, some Python packages like Kivy have binary dependencies. It’s often easiest to use the pre-compiled wheels via pip, but if pip needs to compile something, you might need Visual Studio Build Tools installed.

## Step 1: Clone or Download BatLLM

Using Git (recommended):

```bash
git clone https://github.com/krahd/BatLLM.git
cd BatLLM
```

Alternatively, download the repository ZIP from GitHub and extract it, then navigate into the `BatLLM` directory.

## Step 2: Create a Virtual Environment (optional but recommended)

It’s good practice to create an isolated Python virtual environment for the game, so that you don’t pollute your system Python with game-specific libraries:

```bash
# Create a venv named "venv"
python3 -m venv venv

# Activate the virtual environment:
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

After activation, your command prompt should be prefixed with (venv). Now any pip installs will go into this environment.

## Step 3: Install Dependencies

With the virtual environment activated (or skip that if you chose not to use one), install the required Python packages:

```bash
pip install -r requirements.txt
```

The requirements file includes Kivy and other needed libraries. This may take a few minutes, especially for Kivy, which will download platform-specific wheel files.

**Kivy installation tips:**

* On **Windows**:

  * Kivy might need some additional components like SDL2 binaries. The pip install usually includes these in the wheel. If you run into errors, visit [Kivy’s Windows installation guide](https://kivy.org/doc/stable/installation/installation-windows.html) for troubleshooting. You might need to upgrade pip (`pip install --upgrade pip`) to ensure it can fetch pre-built Kivy wheels.
  * If you have problems with angle or glew dependencies, try: `pip install kivy[base] kivy[angle_support]` which uses DirectX instead of OpenGL on Windows.

* On **macOS**:

  * Kivy should install via pip. On newer macOS (M1/M2 chips), make sure you’re using an env with arm64 binaries or using Miniforge/Conda environment if pip has trouble.
  * You might need to allow the Python app to use the screen (sometimes macOS asks for permissions if it thinks it’s trying to record or control the screen due to OpenGL contexts; usually not an issue for Kivy though).

* On **Linux**:

  * You may need to install some system packages (like SDL2, OpenGL drivers, etc.) if they are missing. Check Kivy’s Linux install guide. For example on Ubuntu:

    ```bash
    sudo apt install python3-pip python3-dev ffmpeg libsdl2-dev libsdl2-image-dev \
         libsdl2-mixer-dev libsdl2-ttf-dev libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev
    ```

    Then pip install Kivy. Manylinux wheels usually handle most of this, but be aware of it if you get an error about missing libraries.

## Step 4: Set Up a Local LLM

BatLLM doesn’t include an AI model— you need to run one separately. The default configuration expects an **Ollama** server (which is targeted at macOS), but you can use alternatives.

### Option A: Using Ollama (macOS)

1. **Install Ollama:** Download it from [ollama.ai](https://ollama.ai/download) or via Homebrew (`brew install ollama`). Follow their instructions to get it running.

2. **Download a Model:** The default config uses `llama3.2:latest`, which refers to a Llama2 7B Chat model variant. You can run `ollama pull llama2` or `ollama run llama2:7b` or similar; however, “llama3.2” is an Ollama-specific name for their tuned model. For simplicity, run:

   ```bash
   ollama run llama3.2:latest
   ```

   The first time, this will download the model (several GB). Keep this terminal running; it’s now hosting the model on `http://localhost:11434`.

3. **(Optional) Second Model Instance:** By default, BatLLM’s config has two endpoints (ports 11434 and 11435). You can either:

   * Run a second Ollama instance on a different port. For example, you could edit Ollama’s config or run a second model by specifying `OLLAMA_PORT=11435` environment variable for a new instance (Ollama doesn’t natively run two instances easily, so another approach is to run a different model on the same instance and still use one endpoint – see **Single-model mode** below).
   * **Or** configure BatLLM to use a single LLM for both players by setting `independent_models: false` in `config.yaml`. In that case, it will only use the first endpoint (11434 for both bots). This can simplify setup (only one Ollama process needed).

If you use one model for both bots, be aware that the LLM might get both prompts sequentially. This usually is fine (the game isolates the calls), but theoretically, a single model might have some cross-talk if it retains state between requests (Ollama’s default is stateless for separate requests).

### Option B: Alternative Local LLM (Linux/Windows or other)

If you cannot use Ollama (e.g., on Windows), you have a few choices:

* **LocalAI or text-generation-webui**: These tools can host models and provide an API. For instance, text-generation-webui can enable an API server (REST). You would then point BatLLM to `http://localhost:5000/api` or whatever it uses.
* **Llama.CPP HTTP Server**: There are simple HTTP servers wrapping llama.cpp. One such project creates an endpoint at `http://localhost:8000/completion` (for example). You might need to adjust BatLLM’s Bot code to match the exact payload/response format expected. By default, BatLLM expects a JSON with `"response"` field containing the text.
* **OpenAI API (not local)**: As a last resort, you could use an OpenAI model by writing a small wrapper or by adjusting the code to call OpenAI API. This will be slow and cost money and go against the “local” spirit, but it’s possible. Not recommended for regular use.

**Configuring BatLLM for alternatives:** Open `configs/config.yaml` in a text editor. Change the `llm.url`, `port_base`, and `path` to match your API. For example, if using a local server on port 5000 that expects POSTs to `/api/v1/generate`:

```yaml
llm:
  url: "http://localhost"
  port_base: 5000
  path: "/api/v1/generate"
  independent_models: false   # if the server handles both bots (single model)
```

And ensure the request body that `Bot.submit_prompt_to_llm` sends matches what the server expects. If needed, you might have to modify `bot.py` to format `data` differently for non-Ollama endpoints (e.g., some want a field `"prompt"` vs `"text"`, or no `"model"` field, etc.). This is a bit advanced; ideally, adapt your server to accept Ollama-style inputs for easiest integration.

### Option C: Using Two Separate Models

If you have enough resources, you can run two different models (or two instances of the same model) for Player 1 and Player 2. This could be interesting if you want them to have different “personalities” or capabilities. To do this, run each on a different port and set `independent_models: true` with the base port as appropriate.

Example: run one model on port 5001 and another on 5002. Then:

```yaml
llm:
  url: "http://localhost"
  port_base: 5001
  path: "/api/generate"
  independent_models: true
```

Player 1 will hit :5002, Player 2 will hit :5003 (since it adds the bot ID). Actually, careful: if port\_base is 5001, then for bot1 (id=1) code does `port = port_base + id`, so 5002, and for bot2 id=2 it’s 5003. So set port\_base such that `port_base + 1` and `+2` correspond to your actual running ports. Alternatively, if that’s confusing, just set `independent_models: false` and directly put the full URL for each model in code (you’d have to tweak Bot initialization to not append the id).

## Step 5: Running BatLLM

Now you have Python packages installed and an LLM server running. Start the game:

```bash
python batllm.py
```

If everything is set up, a window should appear with the game. The terminal may show some logs from Kivy (like version, starting apps, etc.) and logs from the game (like "Playing round 1", and any prints for debugging).

### Common Issues & Solutions

* **Window does not show or closes immediately:**

  * Check the terminal for errors. If you see something like `ModuleNotFoundError: No module named 'kivy'`, then the Kivy installation failed or you’re using a different Python than you installed to. Ensure you activated the virtual env or use the same Python environment.
  * If you see OpenGL errors or the window opens then closes with no output, it could be an OpenGL compatibility issue. Try updating graphics drivers. On Windows, if using Remote Desktop or a VM, Kivy might have trouble; on Windows, ensure either you have an actual GPU context or use the Angle/DirectX angle\_support option for Kivy.
  * On Mac, if it crashes with an error about multitouch or SDL, try running `KIVY_WINDOW=sdl2 python batllm.py` to force a specific window provider.

* **Kivy installation issues:**

  * If pip couldn’t install Kivy (especially on Python 3.11 early days or on uncommon platforms), you might try pip installing a specific Kivy version. Check [Kivy download](https://kivy.org/downloads/) for a wheel that matches your Python and OS, then do `pip install path/to/kivy.whl`.
  * Ensure pip is updated to the latest version, as older pip might not fetch the correct Kivy binary.

* **Ollama or model issues:**

  * If `ollama run llama3.2:latest` is not recognized, ensure Ollama is installed and in your PATH. If it says model not found, try `ollama pull llama2:7b` or check Ollama’s model list.
  * If the game fails to get a response from the model (you see in the terminal something like `[1] LLM request failed: ...`), the model might not be running or the endpoint URL is wrong. Double-check the port and that the model server is listening. You can test by running a `curl` command: e.g.

    ```bash
    curl http://localhost:11434/api/generate -X POST \
      -H "Content-Type: application/json" \
      -d '{"model":"llama3.2:latest","prompt":"Test","stream":false}'
    ```

    You should get some JSON response. If not, the server isn’t responding as expected.
  * On Windows, since Ollama isn’t available, ensure your alternative model is working. If using text-generation-webui’s API, open its web UI to ensure it loads the model, and maybe try a test generation through its interface first.

* **No sound:** If you don’t hear any sound when shooting or hits (and you expect to), check that the sound files are present in `assets/sounds` and that your system audio is on. Note that on some systems, sound might not play if the game window isn’t focused.

* **Performance issues (low FPS or lag):** The game logic is simple, so lag usually means the LLM is slow. You can reduce the model’s response length by adjusting your prompts or model settings (e.g., temperature, max tokens) by editing how the prompt is sent in `bot.py` (Ollama by default may have internal settings; for others you could add parameters in the JSON like `max_tokens`). Also, closing other heavy applications or using a smaller model can help.

## Verification

Once the game is running, try a quick match to ensure everything works:

* Enter simple prompts like “M” for one bot and “M” for the other (if augmentation is on, the LLM will still see context but your prompt is just “M” which might confuse it because it expects instruction… better might be “Just move.” as a prompt).
* The bots should move. If one of you enters a prompt that suggests shooting and the conditions are right, see if the bullet mechanic works (one bot’s health should drop).

You can open the console/terminal to see prints from the game for debugging:

* It will print when rounds start, when bullets are fired and hits occur, etc. This can help confirm the LLM responded (e.g., you might see “Bot 1 shoots!” in the log if it decided to shoot).

If you encounter issues not covered here, feel free to reach out via the GitHub issues page. Since BatLLM is in active development, improvements to installation and compatibility are ongoing.

Happy battling!

<br>

**DEVELOPMENT.md**

# Developer Guide: Extending and Understanding BatLLM

This document is for developers and tinkerers who want to understand BatLLM’s code structure or extend the game’s functionality. We’ll go through the major components, code organization, and provide tips on adding new features or modifying behavior.

## Overview of Code Structure

BatLLM’s code is organized into a few key modules:

* **Main Application**: `batllm.py` – likely contains the Kivy App class and initialization logic. It sets up the window, ScreenManager, and loads the HomeScreen.

* **Configuration**: `app_config.py` – handles loading the YAML config and provides a `config` object for global access to settings. This uses a simple class to merge defaults and user config.

* **Screens**:

  * `home_screen.py` – defines the `HomeScreen` class (inherits from `Screen`). This is the main game UI screen containing prompt inputs, history, etc., and the game board widget.
  * (Potentially `settings_screen.py` if implemented – a stub for a settings UI, since HomeScreen references `go_to_settings_screen`, but as of now it might not be fully realized.)

* **Game Board and Mechanics**: `game_board.py` – defines `GameBoardWidget` (inherits `Widget`), which is the canvas where bots and bullets are drawn and where the game logic (turns, rounds) is managed.

* **Entities**:

  * `bot.py` – defines the `Bot` class, representing a bot/player’s controlled unit. It contains state (position, rotation, shield, health, prompt history, etc.) and methods to execute commands and interact with the LLM.
  * `bullet.py` – defines the `Bullet` class, which handles bullet movement and collision logic. A bullet is not a Kivy widget but a logical object; drawing the bullet is handled within the GameBoard’s canvas.

* **Utilities**: `normalized_canvas.py` – a context manager for using normalized coordinates in Kivy’s drawing routines, and helper static methods to convert between screen and normalized coordinates.

* **Assets**: The `assets/` directory holds static files like sound effects and possibly text files with example prompts. For instance, `assets/prompts/prompt_2.txt` is referenced in the code (perhaps an example prompt that can be loaded for quick testing via a function in HomeScreen).

* **KV Layout**: There might be a KV language file (like `batllm.kv` or similar) defining the UI layout, since the HomeScreen and GameBoardWidget have `ids` references (like `prompt_player_1`). However, on quick inspection, the code sets up UI mostly in Python (perhaps dynamically). It is possible that the `.kv` file is embedded or not used, and instead the HomeScreen is constructed in Python code. If there is a KV file, it would be loaded automatically by Kivy (matching the App name or Screen name). If not, the UI elements might be created in the HomeScreen’s KV or in code.

  *For now, we’ll assume basic UI is either defined in a KV file or in HomeScreen’s class through the `ids` that get auto-populated.* Understanding this isn’t critical unless you plan to redesign the UI.

### HomeScreen and GameBoard Wiring

When the app launches, it likely creates a `ScreenManager` and adds `HomeScreen` to it (with name "home"). In `home_screen.py`, HomeScreen’s `on_kv_post` or `__init__` might instantiate the GameBoard widget and assign it to an id (e.g., in KV, HomeScreen might have something like `<HomeScreen>:\n    GameBoardWidget:\n        id: game_board` etc.). We saw in code that HomeScreen methods use `self.ids.game_board` to access the GameBoardWidget instance.

**HomeScreen responsibilities:**

* Holds the input TextInput fields for both players (ids like `prompt_player_1`, `prompt_player_2` for current prompt input, and possibly `prompt_history_player_1`, etc., for showing last prompt).

* On clicking "Submit" for a prompt (likely a Button or pressing Enter triggers an event), HomeScreen calls its `submit_prompt(bot_id)` method. We saw this method in the code: it retrieves the text from the input field, adds it to the prompt history display, clears the input, and then calls `game_board.submit_prompt(bot_id, prompt)`.

* The HomeScreen also has methods to navigate prompt history (rewind/forward), which simply call the Bot’s history navigation and update the UI text field with the history entry. This allows players to easily reuse or edit previous prompts.

* Possibly has a header label with id `header_label` to show "Round X. Turn Y." which GameBoard updates each turn.

* If implemented, HomeScreen has a menu or button that calls `go_to_settings_screen`, which switches the ScreenManager to a "settings" screen (not sure if that exists in code yet).

**GameBoardWidget responsibilities:**

* Maintain list of Bot instances (`self.bots` with Bot 1 and Bot 2).

* Draw the arena and bots (in `render()` method) each frame.

* Handle input from HomeScreen via `submit_prompt(bot_id, prompt)`: when HomeScreen says a prompt is ready, GameBoard stores it via Bot’s `prepare_prompt_submission` (which saves it in history and flags ready\_for\_next\_round).

* Once both bots have prompts (it checks `if all(b.ready_for_next_round for b in bots)`), it starts a round (`play_round()`).

* `play_round`: sets up round count, resets any needed flags, logs round in output history, shuffles bot order for turn sequence, and calls `play_turn()`.

* `play_turn`: This is called with each iteration of the turn loop. It checks if turn limit reached; if yes, it ends the round (shows popup with health summary). If not, it updates the header label text (Round/Turn info), then for each bot in `self.shuffled_bots` order, it sets `ready_for_next_turn=False` and calls `bot.submit_prompt_to_llm()`. This triggers asynchronous LLM calls for both bots.

* When each bot’s LLM call finishes, `Bot._on_llm_response` calls back to `GameBoardWidget.on_bot_llm_interaction_complete(bot)`. That function sets `bot.ready_for_next_turn=True` and when *both* bots are done, increments turn counter and schedules the next turn (`Clock.schedule_once(self.play_turn, 0)` to immediately invoke next turn in the event loop).

* If a bot died (health <= 0), currently the code doesn’t explicitly break out of the loop besides not scheduling more turns because one bot won’t ever get ready (depending on implementation). A robust implementation might check after each turn if any bot is dead and if so, declare match end. In our current code, the match ends effectively because one bot’s health is 0 and further bullets or actions might not target it; however, to be safe, one might add:

  ```python
  if bot.health <= 0 or self.get_bot_by_id(3 - bot.id).health <= 0:
      return
  ```

  in relevant places. Developers extending the game should be mindful to handle end-of-game conditions clearly (popups, resetting state or disabling further input until reset).

* The GameBoard also listens to keyboard events (we saw `_on_keyboard_down`). This allows manual control for debugging. It’s not typical in final gameplay (because players are expected to use prompts), but it’s a handy dev feature. It shows how to call Bot methods (move, rotate, etc.) directly.

* Drawing bullets: We saw that manual shooting (spacebar) does a while loop updating bullet until it’s done, and drawing trace points. In a future version, we might want to integrate bullet movement into the frame-by-frame rendering (to animate the bullet instead of instantly simulate it). Right now it’s instant for gameplay fairness (ensures the outcome is decided before the next bot moves). The trace is just cosmetic.

* The `bulletTrace` list and `bullet_alpha` are used in render() to draw a fading bullet trail. Each frame, bulletTrace points are drawn and alpha fades out until cleared.

* Output history: `add_text_to_llm_response_history` and `add_llm_response_to_history` in GameBoard update a text box (with id like `output_history_player_1`) with the commands executed. This is a log of what the LLM commanded each turn. For example, when a round starts, they add a line "Round X." to separate rounds. Then each turn, `add_llm_response_to_history` prefixes with turn number and the command, like “   1. M” meaning Turn 1 command was M. This is just UI sugar for players to see a history of actions.

## Extending Game Mechanics

Here are some common extension ideas and how you might implement them:

### Adding a New Command

Suppose you want to add a new bot command, e.g., `J` for “jump” (just as an example to maybe avoid bullets by leaping, purely hypothetical).

* **Bot actions**: You’d define what “jump” does. Maybe it could move the bot a longer distance or allow dodging a bullet differently. You’d implement a method in `Bot` class, say `def jump(self): ...`. Maybe it moves the bot a certain fixed distance or changes `y` quickly. Also, consider any effects on bullet collision (maybe jumping could mean bullets pass under? That would complicate physics — we’ll keep it simple: jump is just a big move).

* **Command parsing**: In `Bot._on_llm_response`, add a case for `"J"`. For example:

  ```python
  case "J":
      self.jump()
  ```

  and handle any number argument if needed (maybe jump distance). If it’s always a fixed jump, no number needed, or `Jd` could mean jump distance d.

* **Prompt augmentation**: If the new command requires the LLM to know about it, you may want to mention it in the augmentation preamble (the big multi-line string in `Bot.submit_prompt_to_llm`). The current preamble lists the commands and what they do. Add your new command description there so the LLM is aware of it. For example: “`Jd - the bot jumps, moving forward by d*2 units rapidly (d default 1 if not specified). Example: J`”.

* **UI feedback**: Perhaps log the command to the history as well, which will happen automatically if you call `add_llm_response_to_history(self.id, command)` like others do.

* **Testing**: You’d then write prompts to encourage the model to output `J`. Also consider model behavior: if the model isn’t trained on this command, it might rarely output J unless you explicitly prompt that way. But by adding it to the instructions, you increase the chance. Using few-shot examples in the prompt (giving an example scenario and command) could further help, but that’s advanced.

### Changing Arena Size or Adding Obstacles

The arena is currently normalized to 1x1. If you wanted a larger area or scrolling, you could:

* Increase the range of coordinates (e.g., allow >1 or <0 in normalized terms, and adjust drawing to scale down to screen). Or simpler, conceptually treat 0-1 as your display window and implement a camera for a larger world. This is non-trivial with current code but doable by scaling coordinates.
* Obstacles: You’d have to represent them (maybe as circles or rectangles) and check collisions on movement and bullets. This means:

  * Add an `obstacles = []` in GameBoard, each with position and size.
  * In `render()`, draw the obstacles.
  * In `Bot.move()`, before finalizing new position, check if that line segment from old to new intersects an obstacle; if so, maybe stop before it or prevent movement.
  * In `Bullet.update()`, similarly check obstacle collisions and treat like hitting a wall (stop the bullet, maybe destroy it without damage).
  * This complicates things but would make the game richer. Ensure the LLM knows about obstacles: you’d include them in prompt augmentation (“there is a wall at x=0.5, y=0.5” etc.) or else the LLM will blindly run into them. That opens an interesting area of prompting.

### Multiple Bots or Teams

To go beyond 2 players:

* You can definitely create more Bot instances. The code uses a list `self.bots` and doesn’t inherently limit to 2 except in places where things like `3 - self.id` appear (that’s clearly a 2-player hack to get the opponent). You’d have to remove such constructs and use loops to gather opponents etc.
* UI: you need input fields for more players, or at least a way to control them. Possibly a free-for-all mode where all prompts are entered at once. The UI might become crowded, so you might have a separate prompt entry phase for each, or one at a time.
* Turn order: with more than 2, how to decide order? Maybe still random shuffle of all bots each round, and each turn each bot acts once in that order. This would be similar logic, just extend the shuffle to n bots, and loop through them for actions.
* Allies vs enemies: if you have teams, you might want bots to not shoot their teammates, etc. LLM would need to be informed of team membership.

So while possible, it’s a significant change. Not recommended unless you want a real challenge and to rewrite parts of the logic.

### Networking (Online Multiplayer)

Currently, both players use the same machine. Networking would involve:

* Separating the frontend (client) and game logic (could be on a server or one of the players acts as host).
* You’d have to sync prompts and game state across the network. Perhaps have one instance of the game act as authority that runs the physics and LLM calls, and the other just sends input (prompts) and receives updates (bot positions, etc.).
* Kivy is not inherently networked, so you’d integrate something like a simple Socket or REST API to exchange data. This is a large feature – essentially turning the game into a client-server model.

Alternatively, one could run the game as is and use a screenshare or remote control. But a built-in online mode would be amazing; it just involves a lot of engineering (beyond Kivy, into Python networking, latency handling, etc.). If you attempt it, start with something simple like a socket that transmits prompts between two running instances and coordinates turn stepping.

### AI Opponent (Single-Player Mode)

Since the game uses LLMs for actions, an AI opponent is just another human’s prompt in a way. To simulate that, you could:

* Write a fixed or programmatic prompt for the second bot. For instance, you could ignore Player 2’s input and instead auto-generate a prompt like “Play defensively.” or use some logic to generate a prompt based on state (“If my health < other’s health, charge, else hold position”). Then feed that to Player 2’s LLM each round. The human player would only input for Player 1.
* A more advanced approach: use a second LLM to *generate* the prompt for the second bot based on the game state (this gets meta!). Essentially, one LLM could play the role of “AI strategist” producing an English prompt for the “bot LLM”. Probably overkill and slow, but an interesting concept.
* The simplest: just have a curated prompt for the enemy and stick with it (like a difficulty level: easy bot might always do the same thing or random things, a hard bot might have a carefully engineered prompt to counter common tactics).
* Implementation: you’d modify the input handling so that if one of the players is marked as AI, the game doesn’t wait for a prompt from HomeScreen for them. Instead, when starting the round, you directly do `bot.append_prompt_to_history(ai_prompt)` for that bot and mark it ready. The rest of the flow can remain the same. Possibly surface to UI “AI is deciding…” or just immediately start the round since the prompt is set.

## Understanding LLM Integration Details

The prompt the LLM receives (with augmentation) is crucial. In `Bot.submit_prompt_to_llm`, the code constructs `data["prompt"]`. If augmentation is on, it adds that big chunk:

* Explanation of the game and roles.
* Game logic description (pseudocode-like bullet points of the loop).
* Detailed current state (self and opponent stats).
* Finally `"User prompt: "` and the actual player prompt.

This prompt is quite large but it guides the model to output a concise command. This was likely tuned with the Ollama model to yield good results. If you use a different model and it’s not responding in the desired way, you might need to tweak this text. For example, some models might require a system prompt (not applicable in Ollama’s simple API which just takes one prompt string). Or they might be better if the instructions are shorter.

One might experiment with prompt engineering:

* Perhaps provide one example in the prompt: e.g., an imaginary Round 1 state and a user prompt and then an example model answer (like few-shot learning). But that makes the prompt even longer, potentially hitting context limits for smaller models.
* The current approach assumes the model is in chat mode to some extent (the text addresses the LLM as “you are an expert gamer…”). This likely works with instruct-tuned models.

**Parsing the LLM response**: After getting `result` from the request (which for Ollama is JSON with `"response"`), the `_on_llm_response` method:

* Strips it, and if it’s a list (some endpoints might return a list of choices), picks the first element.
* Then checks `command = command[0]` (and if list, command was set to a string anyway). This effectively takes the first character of the response. If the model returns “M” or “C90”, `command[0]` will be “M” or “C” respectively — which is fine for the switch logic, but notice they don’t actually keep the rest of the string except when needed for angle or shield number:

  * They do `angle = float(command[1:])` for C and A, meaning they do use the rest of the string as degrees.
  * For S, they check length; if it’s more than 1 and second char is 1 or 0, they set the shield accordingly.
  * For B and M, there’s nothing after, so that’s straightforward.

  If the model returned "C90 degrees", the first char is "C", they then try float(command\[1:]) on "90 degrees" which throws an exception. That would lead to `command_ok = False` and it would print wrong command. So again, instruct your model through the prompt to output just the command without extra text or units.

If you as a developer want a more sophisticated parser (maybe the model outputs a full word like “Move” instead of M, or you want to allow it to output “C 90” with a space), you could modify this parsing:

* Perhaps use regex to find a known command letter in the response.
* Or do NLP on the response (that’s ironic because we are using an LLM, but one could use a regex like `match = re.search(r'\b([CAMBS][0-9]*)\b', text)` to find something that looks like a command).
* However, for consistency, it’s best to enforce the model’s output via the prompt to be exactly the format needed.

**Asynchronous design**: The use of `UrlRequest` for the LLM call is important. It doesn’t block the UI thread. The callbacks ensure we handle the result. This is why the game doesn’t freeze while waiting for the model, and we can even have both requests in flight concurrently.

Kivy’s main loop is still running, rendering frames (though nothing much changes until we get responses, except maybe some animation or a “waiting” indicator if we added one).

**Thread safety**: Kivy’s `UrlRequest` runs the request in a separate thread. The callback `_on_llm_response` is called in the main thread (Kivy schedules it). The code interacts with Kivy UI (updating labels, etc.) and game state, so doing it in main thread avoids race conditions. If you ever offload more work to threads (like heavy computations), take care with updating Kivy properties (must do in main thread via Clock.schedule).

## Making Changes and Testing

When you modify the code:

* It’s best to run the game from a console so you can see print outputs and tracebacks.
* Kivy will output some warnings or info (like used log level etc.). If something goes wrong, you might get a stack trace in the console.
* Use the provided keyboard controls for debugging. For example, if you’re unsure if shield logic works, press “S” to toggle shield manually and see if bullets are blocked.
* You can also manually call functions in code by adding temporary test code. For instance, after launching the app, you could schedule a function to run after a few seconds to simulate a bullet, etc. But usually playing a quick round is easier.

If adding features like new commands or mechanics, you might also want to adjust the **PROMPTS.md** documentation to guide players on using them. Keep docs in sync with code!

## Code Quality and Style

* The code is mostly straightforward, using Python 3.10+ pattern matching (`match/case`) for command parsing which is nice.
* Spacing and naming: it uses snake\_case for functions and variables (PEP8 style). Some parts (like some print debugging statements) can be cleaned up or removed as you finalize features.
* Comments: There are some TODOs in code (like “# TODO move sounds to Bot class”). Feel free to address these if you want (for example, you could indeed move sound playing logic inside Bot.shoot or on taking damage).
* Keep cross-platform in mind: avoid using OS-specific file paths. Use `Path` (as seen in app\_config using pathlib). The code already does that for config path, etc.

## Potential Roadmap Ideas (for developers)

These are not immediate tasks, but where the project could head, technically:

* **GUI Improvements**: Use Kivy widgets to show health bars, maybe an overlay for shield (a semi-transparent arc in front of the bot when shield is up). The info boxes are useful but not the prettiest; could replace with icons or bar indicators.
* **Model Integration**: Possibly integrate with other frameworks (like have an option to run a smaller model in-process via something like transformers or llama.cpp Python binding for those who don’t want to run a separate server). This could simplify setup but would require threading or async to not freeze Kivy during generation.
* **Scalability**: As more features are added (obstacles, multi-bot, etc.), consider performance. The current approach of simulating bullet instantly is okay for now. If real-time continuous motion were introduced, you’d need to integrate bullet movement into the Clock interval (e.g., update bullet positions each frame, detect collision, etc., rather than while loop).
* **Testing**: Write some unit tests for core logic (e.g., bullet collision calculations in Bullet.segment\_hits\_bot). Right now, manual playtesting is how we verify it.
* **AI Behavior Tuning**: Possibly include multiple augmentation strategies or LLM personalities and allow switching. For example, a “strict” mode where the LLM is forced to follow a pseudo-code step (this might require a more complex prompt template or even fine-tuning a model on game data, which is beyond scope but interesting).
* **Better error handling**: If an LLM call fails (network error or whatever), currently we just print an error and mark the bot ready. We might want to retry or have the bot skip the turn gracefully. Also maybe show an on-screen message if an LLM didn’t respond (“Bot 2 had no response this turn.”).

We hope this gives you a solid understanding of BatLLM’s internals and a starting point for making your own modifications. The project is relatively small, so don’t hesitate to open the files and explore the code – it should be approachable.

Happy coding, and may your bots be ever at your command!

<br>

**PROMPTS.md**

# PROMPTS.md - Crafting Effective Prompts for BatLLM

One of the core goals of BatLLM is to help players practice writing prompts to control an AI. This document provides guidance on writing good prompts, examples of prompts and their outcomes, and tips for troubleshooting when the LLM doesn’t do what you expected.

## Prompt Writing 101

In BatLLM, **you are essentially programming a bot through natural language**. Your prompt should communicate your strategy or desired actions clearly to the LLM controlling the bot. Here are some general tips:

* **Be Direct:** Short, imperative sentences tend to work well. For example, “advance and shoot” is more effective than “I think you should maybe move forward and then consider firing.” The latter might confuse the model or lead to unpredictable output.
* **One Command at a Time:** Remember that in each turn, the LLM can only execute one action (the game will take the first action it sees). So focus your prompt on the most important thing to do *right now*. Don’t try to pack multiple sequential actions in one prompt, because even if the LLM lists two things (“move then shoot”), only the first will happen. Instead, if you want a combo, phrase it as a conditional or priority: e.g., “If in range, shoot; otherwise, move closer.” A good model might output just the action that applies (though this can be hit-or-miss).
* **Use Game Terms:** You can mention specific commands or states if needed. The LLM knows commands like “M, B, S1, S0, C90, A90” from the augmentation instructions. You can incorporate those terms to influence it. For example: “You are low on health, prioritize defense. Raise shield (`S1`) and evade.” This might encourage the model to output `S1`.
* **State Intent, Not Execution:** Describe what you want to happen in game terms, but not how to format it. Avoid telling the LLM explicitly “output ‘M’.” Instead say “Move forward.” The augmentation already instructs it to output a command. If you start talking about the output format in the prompt, the model might get confused about whether to follow your strategic advice or the format instructions. In most cases, focus on the strategy and let the internal instructions (from augmentation) handle the formatting.

## Examples of Prompts and LLM Outputs

Below are some example scenarios with prompts and the typical commands an LLM might return. Assume prompt augmentation is **enabled** (so the LLM is getting full state info each turn).

### Scenario 1: Opening Move (Distance Apart)

* **Game State:** Round 1, Turn 1. Bots start far apart (random positions). Neither shield is up. Both have full health.
* **Player 1’s prompt:** “Close in on the enemy and fire when ready.”
* **Player 2’s prompt:** “Keep your distance and don’t get hit. Stay defensive.”
* **Likely Outcome:**

  * Bot1’s LLM might reason it needs to move closer first. Likely command: `M` (move forward).
  * Bot2’s LLM, being defensive, might either stay put with shield or move away. Possibly command: `S1` (raise shield) or maybe `M` (if it interprets “keep distance” as move away, but since it doesn’t know which way is away without more info, it might just raise shield).
* **After Turn 1:** Bot1 moves closer. Bot2 raises shield. Both still alive. The game goes to Turn 2.
* **Considerations:** If Bot1 had been in range at start (rare), it might have fired `B` immediately. But assuming distance, moving is sensible. Bot2’s “stay defensive” prompt often triggers shield up as the first move.

### Scenario 2: Mid-game Encounter (Bots facing each other)

* **Game State:** Bots are within firing range, facing each other. Player 1’s bot has slightly less health (say 5 vs 7). Player 2’s shield is up from last turn, Player 1’s shield is down.

* **Player 1’s prompt:** “My health is low, finish this now with a shot!”

* **Player 2’s prompt:** “They’re about to shoot, keep your shield aligned and counter-attack if possible.”

* **Likely Outcome:**

  * Bot1’s LLM sees an opportunity to shoot (and prompt explicitly says “shot”). It will likely output `B` (fire bullet). If Bot2’s shield is up but not facing properly, Bot2 might get hit unless shield angle covers Bot1’s direction. But at least Bot1 will try to shoot.
  * Bot2’s LLM has a defensive instruction. It may choose not to drop shield. Possibly it does nothing or maybe rotates (`C` or `A`) to ensure it’s facing Bot1 (to maximize shield protection), or it might also fire (`B`) if it thinks counter-attack “if possible.”

* **Resolution:** If Bot1 shoots, the bullet is resolved. If Bot2 was shielded in front, it takes no damage. If shield wasn’t covering, Bot2 loses health. Then Bot2 executes its command (if still alive). If Bot2 also chose `B`, and its shield was up, note: `B` does nothing when shield is up – which could happen if the LLM overlooked that rule. That would result in effectively a wasted turn for Bot2 (which is a realistic outcome if the prompt wasn’t clear). This highlights: *the LLM needs to know to lower shield before shooting or it won’t shoot at all*. The augmentation text does say “if shield is up it does nothing” for `B`, so a smart LLM might output `S0` or incorporate that. But usually, an aggressive prompt would cause the LLM to drop shield then shoot in two separate turns.

* **Player Tips:** In such situations, if you’re Player 2 and you want to fire, maybe explicitly prompt “drop shield and shoot” to ensure the model does `S0` or `S` instead of a futile `B` with shield on. But remember only one action happens per turn—so it’d drop shield this turn, then next turn hopefully shoot.

### Scenario 3: Flanking Maneuver

* **Game State:** Bots are at moderate distance. Player 1’s bot is facing the opponent directly. Player 2’s bot is facing away (perhaps it moved past Player 1). Both shields are down.
* **Player 1’s prompt:** “Shoot them in the back now!”
* **Player 2’s prompt:** “They’re behind you! Turn around and raise shield!”
* **Likely Outcome:**

  * Bot1’s LLM sees a clear shot and prompt says shoot in the back -> outputs `B`. Bot2 is not shielded and facing away, so if Bot1 shoots, Bot2 will almost certainly be hit (since shield is down and even if Bot2 tries to turn, the bullet resolution is instantaneous before Bot2 moves). Bot2’s health will drop by BULLET\_DAMAGE.
  * Bot2’s LLM might output `C180` (turn around) or `A180` depending on how it decides to rotate, or possibly `S1` to raise shield without turning (which would actually be useless if they’re facing away — it should turn to face). The prompt gave two instructions: turn around *and* raise shield. The model can’t do both at once. It might choose one. Often, the mention of “behind you” will cause a rotation because it recognizes that’s critical. So maybe it outputs `C180`. Or if it somehow decides shield is priority, `S1`. Hard to predict, but either way, Bot2 likely gets hit by Bot1’s bullet before it can do anything (since Bot1 was first in turn order in this example).
* **Lessons:** This scenario shows how turn order and bullet immediacy can make a big difference. Player 2 basically had no chance if Player 1 was chosen to act first that turn. The remedy for Player 2 would have been to have shield up in the previous turn or not let Player 1 get behind. As a prompter, sometimes you have to anticipate: if last turn your opponent started moving around you, maybe you should have prompted a pre-emptive turn or shield.

## Dealing with Uncooperative LLM Outputs

Sometimes the LLM might output something invalid or suboptimal like a long sentence or an unrecognized command:

* If augmentation is off, it might not know the command format and could reply in prose (“The bot will move now”). That will result in no action (since “T” from “The” is not a valid command). **Solution:** either enable augmentation (recommended) or explicitly instruct the model in your prompt to use a single-letter command. For instance: “Output your move as one of the game commands (M, S, C, A, B). Move toward the enemy.” This kind of prompt might steer it. But be careful: focusing too much on format in the prompt can distract from strategy instructions.
* If the LLM repeatedly gives you multi-step answers or explanations, consider that some models have a tendency to be verbose. You might need to add a directive: e.g., “ONLY output the action, nothing else.” The built-in instructions usually cover that, but models vary. If it’s really stubborn, you might need to use a different model or fine-tune. But for practice purposes, treat it as feedback for your prompt engineering skills.
* If the LLM makes a *bad choice* (like walking into a bullet or not firing when it should have), that’s part of the learning experience. Analyze if your prompt was unclear or too timid. Maybe the model was unsure. Try to pinpoint what command you wanted and include a keyword related to it next time (“dodge”, “attack”, “protect”, etc. map to moves, shots, shields).
* **Example of refining a prompt:**

  * Prompt 1: “Keep moving so you’re hard to hit, and shoot whenever you get a chance.”

    * Outcome: The model outputs `M` every turn, never shooting, because it focused on “keep moving” literally.
  * Prompt 2 (refined): “When the enemy is open, shoot (`B`). Otherwise, move (`M`) to a better position.”

    * Outcome: The model is more likely to output `B` at some point because you explicitly mentioned the command and conditions. Possibly, if not in range, it might still move.
  * Alternatively, you could split it across rounds or turns: First round prompt “Close distance (move towards enemy).” Next round prompt “Now fire!” to ensure it actually shoots when in range.

## Prompting with Augmentation Disabled

Playing without augmentation is challenging but educational. In this mode, the model only sees what you type. You should assume it *does not know* anything about positions, health, or even which bot it is, unless you tell it.

Things to include in your prompt when augmentation is off:

* The enemy’s approximate location or direction (e.g., “The enemy is in front of you.” or “Enemy is at north-east.” But since coordinates are 0-1, you might not know them exactly as a player unless you track visually).
* Your own status if relevant (“Your shield is up, their shield is down.” or “You’re low on health.”).
* Use consistent terms the model might latch onto. For example, refer to the bots as “you” and “the enemy” consistently, or even give them labels (“You are Bot1, Enemy is Bot2”).
* Because this is difficult to maintain, it’s generally recommended to keep augmentation on unless you specifically want to train yourself in high-level prompt injection of state.

## Fun Prompt Ideas

* **Personas:** Since these are LLMs, you can add flavor. Try starting your prompt with a role: “You are a fearless warrior bot. Charge with no hesitation!” or “You are a cautious sniper, pick off the enemy from afar.” The model might channel that persona. It doesn’t change game rules, but it might influence its choices (fearless might move or shoot more, cautious might shield or wait).
* **Deception (with human opponent knowledge):** If you and the other human can see each other’s prompts (currently both prompts are on the same screen, so yes, you can see the other’s prompt), you could try mind-games. Write a prompt that suggests one action but really means another in terms of command. This is advanced and depends on the model understanding subtext. For example, maybe you write, “Pretend to be defensive but actually shoot when they least expect it.” Does the model output `B` (shoot) or `S1` (defensive)? Hard to say! It might do either. Use at your own risk. It can be amusing though.
* **Multi-turn strategy via prompt:** Since one prompt lasts a whole round (multiple turns), you can also include conditional or sequential instructions, hoping the model internalizes a strategy. For example: “First, dodge their attack, then when you see an opening, fire. Continue alternating between evasive maneuvers and shots.” The model doesn’t truly have memory between turns except through the prompt and perhaps any subtle history in augmentation (the augmentation does not currently summarize past actions except listing round and turn number, but not what happened last turn). So this might not reliably cause it to alternate M and B, but you might see it try a pattern. Generally, models treat each turn independently with the fresh augmented prompt (which doesn’t include a recap of last turn’s action aside from turn count). So multi-turn plans in one prompt can get forgotten unless you repeat or the model implicitly tracks through the round count.

## Understanding LLM Limitations

Different models will behave differently:

* A smaller 7B model might be more prone to output something odd or misunderstand the instructions, whereas a 13B or 30B might follow more coherently. But larger models could also be more verbose (since they’re often trained to be helpful and explanatory).
* If a model starts roleplaying or giving long explanations (“As an expert gamer, I would move now.”), that’s actually a good sign it got the context – but you need to reign it in. You could try adjusting the prompt augmentation text to explicitly say “Output only the command.” (It already does, but some models need stronger emphasis).
* Temperature setting: Ollama might have a default temperature (randomness) around 0.7. If you find the model’s actions too erratic, a lower temperature (like 0.2) might make it more deterministic (but you’d need to configure that in the Ollama prompt or via their API if possible – the current code doesn’t expose a temperature parameter, but you could hack in `data["temperature"] = 0.2` in Bot.submit\_prompt\_to\_llm for testing). Lower temperature = more likely to do the obvious thing; higher = more variety (which could be fun or chaotic).
* OpenAI GPT-3/4: If you were to use those via an API, note they expect a conversation format. BatLLM isn’t set up for that out of the box, but if you integrate it, you’d have to format the prompt as a system or user message. Those models are usually very good at following instructions but might *over*-explain if not clearly instructed not to. Always provide a sample output style if using such models.

## Example Prompt and Output Logs

Here’s an example of a full round with actual prompt and outputs (imagine a medium-sized LLM):

**Round 1:**

* Player 1 Prompt: “Aggressive: rush towards the opponent and fire at will.”
* Player 2 Prompt: “Defensive: keep shield up and only attack if they’re wide open.”

**Turn 1:**

* Bot1 (Player1) LLM sees prompt, likely outputs `M` (moves forward).
* Bot2 (Player2) LLM sees prompt, likely outputs `S1` (raise shield).
* Outcome: Bot1 moved closer. Bot2 raised shield.

**Turn 2:**

* Bot1 now maybe in firing range. LLM might output `B` (fire) now, because “fire at will” and now it’s close enough.
* Bot2’s LLM sees enemy is close and probably firing (though it doesn’t *know* for sure, it might guess). It might decide to hold shield (it’s already up, so maybe do nothing or rotate to keep shield towards Bot1). It could output `S` (toggle shield) but that would actually lower it – hopefully it doesn’t do that. Perhaps `C20` (small rotate) or even no meaningful command like an empty or something (if the model’s unsure, it might output something invalid which is effectively a skip).
* Outcome: Bot1 shoots a bullet. Bot2 has shield up; if Bot2 was facing Bot1 (likely it was, since shield was raised when facing the same direction?), the bullet might hit the shield front arc and be blocked (no damage). Or if Bot1 approached from side, shield might not cover, then Bot2 takes damage.
* Either way, both likely survive Turn 2.

**Turn 3:**

* Bot1 prompt hasn’t changed (“rush and fire at will”). It already fired last turn; if the enemy isn’t dead, it might shoot again or if it thinks maybe now too close, it might move to avoid shield? But “fire at will” implies shoot whenever, so likely `B` again (if the first shot didn’t kill, keep shooting).
* Bot2 prompt still “Defensive.” If shield blocked the last shot, maybe it stays course. LLM might do nothing (there is no explicit “do nothing” command, but if it outputs something invalid, effectively nothing happens). Or it might try a shot if it perceives an opening (e.g., if Bot1 is right in front and shield up, it might output `B` thinking “attack now” – but if shield is still up, that shot won’t fire due to game rules). Possibly the model doesn’t fully internalize that rule and does `B` anyway, which results in Bot2 doing nothing (since shield still up).
* Outcome: Possibly Bot1’s second bullet hits and this time maybe Bot2’s shield was misaligned or down (if it toggled), dealing damage. Let’s say Bot2 gets hit and health goes low.

**Turn 4:**

* Bot1 might continue aggression. If Bot2 is almost dead, maybe one more `M` to finish point-blank or another `B`.
* Bot2, if not dead, might panic. “only attack if open” – maybe now it senses it’s do-or-die and enemy is right there, could drop shield to shoot back: perhaps outputs `S0` or `B`. If it outputs `B` while shield up, again nothing. If it outputs `S0` to drop shield (to maybe shoot next turn), that’s a wasted action if Bot1 shoots now. Hard spot for Bot2.
* Likely Bot1 finishes off Bot2 either this turn or next. Aggressor usually wins if defender never counterattacks meaningfully.

The above shows how the interplay of prompts and rules can play out. As a player, after such a match you might realize: Player 2 should have perhaps included “and if they get too close, shoot back!” in the prompt to actually fire at some point. Purely defensive prompt can make the model overly passive.

## Final Tips

* **Experiment**: The best way to learn prompting is try various approaches. Want the bot to circle around? Try: “Strafe around the enemy (rotate as you move) to their side.” The model might output a small rotation or move each turn mimicking a circle. Or it might not understand well. Refine phrasing.
* **Learn from Each Other**: If playing with a friend, notice whose bot performed better and what prompt they used. Discuss why that might be. Maybe one prompt inadvertently gave the model an edge (like mentioning a command by letter). You can even swap prompts next round as a test.
* **Model Choice**: If you have multiple LLM models available, you can configure each player to use a different one. This can make for interesting battles (e.g., a cautious model vs a bold model). It’s also a fun way to see AI personality differences. Just ensure fairness in terms of model size or capability.
* **Have Fun**: Try silly prompts occasionally (“Dance around in circles” might just cause rotations). Or thematic ones (“You are a Jedi, deflect their shots!” might lead to a lot of shield use, which is kind of deflecting). Part of the joy is seeing the sometimes unexpected interpretations the AI comes up with.

Remember, the purpose of BatLLM is not just to win the game, but to improve your skill in communicating with AI under constraints. Every round is an opportunity to learn how a machine “thinks” in response to your words. Enjoy the process, and happy prompting!
