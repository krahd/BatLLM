# BatLLM 
***Democratising AI through play***

**BatLLM** is an open-source, two-player, turn-based battle game in which human players control their in-bots indirectly–by giving instructions to AIs which, in turn, interact with the game.

All matches are divided in rounds. Before each round, the players must give the instructions that their AI will follow during the round.

Player must not only learn how to create *prompts* that control the AI (a Large Language Model, or LLM), but also craft winning strategies. 

**BatLLM**'s blending of strategy, language, and AI-driven gameplay provides a safe, fun, and efficient mechanism to help develop a more accurate and intuitive understanding of LLM models' capabilities and shortcomings. The ever-growing presence of AI in our lives and the massive assimmetries of access, wealth, power, and knowledge impose the urgent task of developing alternative strategies to navigate this reality.

We aim to contribute to the social understanding of AI, and to help in the developing of practical skills, fomenting an intuitive understanding of what LLMs are, what they can and cannot do, while highlighting assumptions and processes that trigger exploitative processes.

While this file (**README.md**) tries to cover every relevant aspect of **BatLLM**, more detailed, technical, or speculative information can be found in the [accompanying documents](#accompanying_documents).

## Table of Contents

* [Project Goals](#project-goals)
  
* At a Glance
	* [Quick Start](#quick-start)
	* [Features](#features)
	* [How It Works](#how-it-works)

* [Game Overview](#game-overview)
	* [Rules](#rules)
	* [Game Flow](#game-flow)
	* [Bot Command Reference](#bot-command-reference)
	* [Prompting](#prompting)

* Using BatLLM
	* [User Guide](#user_guide)
	* [Modes and Variations](#game-modes-and-variations)
	* [Installation](#installation)
	* [Configuration](#configuration)
	* [System Requirements](#system-requirements)
	

* Contributing
	* [Contributing](#contributing) [Development & Contributing](#development--contributing)
	* [Technical Notes](#technical-notes)
	* Data 
	* [License](#license)
	  
* Credits
	* [Acknowledgments](#acknowledgments)
	* Credits [About the Author](#about-the-author)

* [FAQ](#faq)

* Further Reading
	* Installation
	* Contributing
	* Prompting
	* NTFAQ



---
## Project Goals

**BatLLM** is designed as a tool for:

* **Practicing LLM Control:** Experiment with prompts and observe how LLMs interpret and execute them.
* **Developing Prompting Intuition:** See firsthand the strengths and weaknesses of LLMs in understanding and acting on your instructions.
* **Democratising AI Skills:** Enable anyone to interact with advanced language models in a fun, private, and accessible way. No money, connectivity, AI or programming expertise required.
* **Having fun:** A main goal of the project is to create a game that is fun to play.


---
## At a Glance
### Quick Start

1. **Requirements**
    - C++ compiler (C++17+)
    - [Ollama](https://ollama.ai) or another supported local LLM server
    - (Optional) CMake for building main program

2. **Clone & Build**
    ```bash
    git clone https://github.com/krahd/BatLLM.git
    cd BatLLM
    mkdir build && cd build
    cmake ..
    make
    ./batllm
    ```

3. **Running the Game**
   - Start your local LLM servers (see next section).
   - Follow the prompts in terminal to enter your custom prompts each round.
   - Watch the battle unfold!


## Features


### How It Works

1. **Setup**: Each player is assigned a bot. Each round, both enter a prompt—this may instruct their bot either directly or in a role-play fashion.
2. **LLM Mediation**: The game sends the current state and the player's latest prompt to the player’s LLM.
3. **Command Selection**: The LLM generates a single command (like move, turn, shoot, raise shield...) for its bot.
4. **Game Loop**: 
    - A starting player is chosen randomly each round.
    - Bots act, round-robin style, for `ROUND_LENGTH` turns (or until one bot dies).
    - Each turn, the game relays the results to the players for the next round of prompt crafting.

### How It Works

BatLLM acts as an intermediary between the players and their in-game bots. The core loop, managed by the `GameBoardWidget`, is as follows:

1.  **Player Input:** At the start of a round, each player writes a prompt for their bot in the UI (`HomeScreen`).
2.  **LLM Mediation:** For each turn, the game sends a request to an LLM. This request contains the player's prompt and, if enabled, a structured block of game state data (`get_augmented_prompt` in `bot.py`).
3.  **Command Generation:** The LLM interprets the input and generates a single-line command for the bot.
4.  **Command Execution:** The `Bot` class receives the LLM's response (`on_llm_response_received`). It parses the response to find a valid command and executes the corresponding action (e.g., `move()`, `rotate()`, `shoot()`).
5.  **State Update:** The game world is updated, and the changes are rendered on the Kivy canvas. This cycle repeats for each bot every turn.


---
## Game Overview

BatLLM is a two-player competitive game where each player controls a bot by writing prompts. At the start of each round, both players enter a prompt. The prompt (along with optional game state data) is sent to an LLM, which returns a command for the bot. The goal is to destroy the opposing bot by reducing its health to zero through strategic movement, rotation, shielding, and shooting.

### Game Flow and Rules

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

***Example:***
\_Player 1 and Player 2 start Round 1 by entering their prompts. Suppose Player 1 writes: "Advance toward the enemy and fire when in range," and Player 2 writes: "Keep your shield up and evade attacks." At the first turn, the game randomly picks a starting bot. If Player 2’s bot goes first, its LLM might interpret the prompt and return `M` (move forward). The bot moves. Then Player 1’s bot’s turn: the LLM sees the distance closed by the opponent and might return `B` (fire bullet). The bot fires, and if Player 2’s bot is within range and not facing the shot with shield, Player 2’s bot takes damage. The turn ends and Turn 2 begins, now with Player 1’s bot acting first (since order was random per round). The battle continues until one bot is destroyed. At that point, the game ends immediately with Player 1 or Player 2 as the winner. If neither is destroyed after the maximum turns of the round, a new round would start with players possibly writing new prompts based on what they learned.\*


### Game Rules
* Each player enters a prompt **per round** (not each turn). The same prompt will guide the bot for the duration of that round’s turns.
* Each bot executes commands as interpreted by its LLM, one command per turn.
* The arena and bot states are visualised via a Kivy-based interface in real time.
* The match ends immediately when one bot’s health is reduced to zero (the other bot wins). If neither is destroyed within the allotted rounds, the player with more health (or other agreed condition) could be considered the winner (though currently the game assumes sudden-death on bot destruction).

###  Game Rules

- **Bots**:
  - Each has an `x, y` position, a rotation (`a`), shield state (`s`), and health (`h`).
  - Health starts at `INITIAL_HEALTH`. When `h` reaches 0, the bot dies.

- **Turns & Rounds**:
  - Before each round, both players input prompts, which are given to their LLMs.
  - Each turn, both bots receive commands from their respective LLMs and execute them.
  - The round ends after a preset number of turns or when a bot is destroyed.

- **Commands** (from LLM output):
  - Only recognized commands are executed (see below). All else is ignored (no action).

- **Combat**:
  - If a bot fires (`B`) and its shield is down, a bullet is simulated, potentially damaging the other bot unless blocked by a shield (front-facing only).
  - When fired upon, the bot cannot move until the projectile hits or leaves the field.

- **Shield Mechanics**:
  - Shields can be up (`S1`), down (`S0`), toggled (`S`), or left unchanged.
  - Only the front arc (±`SHIELD_SIZE` degrees) is protected.


---
## Usage

* **Home Screen (`home_screen.kv`):**
    * **Prompt Inputs:** Type your prompts for Player 1 (left) and Player 2 (right).
    * **Prompt History:** Below the input, a read-only field shows your past prompts. Use the arrow buttons to navigate and the copy button to reuse a prompt.
    * **Game Board:** The central area where the game is visualized.
    * **Footer Controls:** Buttons to start a "New Game", "Save Session", and access "Settings".
* **Settings Screen (`settings_screen.kv`):**
    * Use the sliders and checkboxes to configure game parameters.
    * Click "Set and return" to apply the settings and go back to the game.
    * Click "Save as defaults" to write the current settings to the configuration file.

### Configuration

Game parameters are managed in `app_config.py` and can be adjusted live from the **Settings Screen**.

* **`total_rounds`**: The number of rounds in a match.
* **`turns_per_round`**: The number of turns in each round.
* **`initial_health`**: The starting health for each bot.
* **`bullet_damage`**: The amount of health a bullet removes.
* **`shield_size`**: The angular size (in degrees) of the bot's front shield.
* **`independent_models`**: (Boolean) If true, uses separate LLM endpoints for each bot.
* **`prompt_augmentation`**: (Boolean) If true, adds game state data to prompts.
* **LLM Endpoints:** The URL and port for the LLM server(s).





### Bot Commands Reference

| Code   | Action                                                                    | Example | Notes                               |
|--------|---------------------------------------------------------------------------|---------|-------------------------------------|
| `Cd`   | Rotate **clockwise** by `d` degrees.                                      | `C20`   | e.g. `C180` for 180° clockwise      |
| `Ad`   | Rotate **anticlockwise** by `d` degrees.                                 | `A40`   | e.g. `A90` for 90° left             |
| `M`    | Move ahead by one step (`STEP_LENGTH`).                                   | `M`     | One forward move per command        |
| `S1`   | **Raise shield**. Remains up until changed.                               | `S1`    |                                     |
| `S0`   | **Lower shield**. Remains down until changed.                             | `S0`    |                                     |
| `S`    | **Toggle shield**: raises if down, lowers if up.                          | `S`     |                                     |
| `B`    | **Fire bullet** (if shield down). Does nothing if shield up.             | `B`     | Bullet direction: bot's facing      |
*Any other output from the LLM is interpreted as 'do nothing' this turn.*

### Modes and Variations

* **Standard Mode:** Each player writes a prompt at the beginning of a round; both prompts are sent to their respective LLMs each turn of that round.
* **Prompt Augmentation:** Optionally, the game augments the player's prompt with structured game state info (see [Prompt Augmentation](#prompt-augmentation)).
* **LLM Assignment:**

  * *Separate LLMs:* Each player’s prompt goes to a different LLM instance (e.g., two Ollama servers on different ports, one per bot).
  * *Single LLM:* Both prompts are handled by a single LLM (the same model) in each turn, which can be useful for lower resource usage or interesting interactions but may risk cross-talk between the two bots’ instructions.

**Note:** There are **no** fully autonomous or AI-vs-AI modes. BatLLM is strictly human-vs-human; all gameplay decisions are made by human-written prompts, then carried out by LLMs. (However, a human player could conceivably write a prompt like *"Play both sides of the battle for me"* and observe what happens, for experimental purposes.)


### Prompting

Each LLM receives a system/user prompt like:

```
You are an expert gamer. Your task is to control a bot in BatLLM, a two-player battle game where an LLM like you controls a bot. You receive information about the game state and a prompt written by the human player that guides your behaviours.

<Game State>
Bot position: (x=..., y=...), angle=..., shield=..., health=...
Opponent position: (x=..., y=...), angle=..., shield=..., health=...

<Player's Custom Prompt>
Try to dodge the next bullet, then retaliate when the enemy's shield is down.
```

*The LLM should respond with a valid command for the bot, e.g. `C90`, `M`, `B`, etc.*


---
## Using BatLLM

### User Guide

### Game Modes 

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

Players can toggle Prompt Augmentation in the configuration. It is highly recommended for beginners, as it makes the LLM’s behaviour more predictable and the game more about strategy than memory.

### Installation

### Configuration

### System Requirements

* **Operating System:** BatLLM is written in Python and uses Kivy, so it should run on macOS, Linux, and Windows. It has been primarily tested on macOS (M1 chip). On Windows, ensure you have the proper environment for Kivy (see Kivy’s docs) and a way to run a local LLM (Ollama is macOS-only as of writing, so Windows users might use an alternative like the Llama.cpp server or HuggingFace Text Generation Inference).
* **Hardware:** There are no specific hardware requirements beyond what’s needed to run the chosen LLM. The game itself is lightweight. However, running LLMs can be CPU/GPU-intensive. For example, Llama2 7B can run on an 8GB RAM machine but anything larger may require more RAM or GPU acceleration.
* **Python:** 3.8 or higher. Python 3.11 is recommended. Ensure Kivy is installed properly for your Python version.
* **Graphics:** Kivy handles graphics via OpenGL. On desktop platforms, a functioning OpenGL drivers setup is required. On most systems this is fine out of the box. If you encounter a black window or crash on startup, it might be related to graphics drivers or missing dependencies for Kivy.
* **LLM Model:** A local LLM runtime such as Ollama or an OpenAI-compatible API. No internet connectivity is required during gameplay except for downloading the model initially.


---
## Contributing

### Notes


* **Indirect Bot Control:** Guide your bot's actions by writing natural language prompts for an LLM.
* **Real-time Kivy Visualization:** The battle unfolds in a 2D arena powered by the Kivy framework, with a normalized coordinate system for easy customization.
* **Turn-Based Strategy:** Plan your moves and prompts round by round in a competitive two-player environment.
* **Highly Configurable Gameplay:** From the settings screen, you can adjust the number of rounds, turns per round, bot health, bullet damage, and shield size.
* **Advanced Prompting Options:** Choose to send raw prompts or augment them with real-time game state data to give the LLM more context.
* **Flexible LLM Setup:** Use a single LLM for both bots or assign a separate, independent LLM to each player.
* **Prompt History & Management:** The UI keeps a history of your submitted prompts. You can navigate this history, copy old prompts, and even load prompts from files.
* **Session Recording:** Save the entire history of a game session, including every turn, prompt, and state change, to a JSON file for later analysis.

- Turn-based, two-player competitive gameplay
- Each bot is controlled by a local LLM (like 'llama’ variants)
- Players influence their bot's behaviour via **creative prompts**
- LLMs receive structured game state and a player-written prompt for context
- Intuitive, minimal command set for bots (see [Bot Command Reference](#bot-command-reference))


* **Human-vs-Human Only:** All players are humans; there are no AI/autonomous players. Every action is mediated by an LLM based on each human player’s prompt.
* **Prompt-Driven Gameplay:** Players write natural language prompts to guide their bots, with the LLM translating these into in-game actions.
* **Local LLM Integration:** Works out-of-the-box with [Ollama](https://ollama.ai) and the `llama3.2:latest` model (tested on an M1 MacBook Pro). The system is model-agnostic and can be configured for other local LLM servers.
* **Prompt Augmentation:** Optional feature that structures and augments the prompt sent to the LLM with game state info for improved control and transparency.
* **Configurable LLM Mediation:** Supports two separate LLMs (one per player) or a single shared LLM (for experimentation or hardware constraints).
* **Intuitive Arena Graphics:** Uses [Kivy](https://kivy.org) for visualization, with a normalized coordinate system for easy customization and creative coding.
* **Modular and Extensible:** Clean, well-documented code ready for expansion (e.g., online play, larger arenas, more complex mechanics or additional bots).


### ### Development

Please refer to **DEVELOPMENT.md** for a detailed documentation.

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


## Technical Notes
  
- **Arena Rendering:** Uses Kivy’s `NormalizedCanvas`—all positions are floats from 0.0 (top/left) to 1.0 (bottom/right).

- **LLM Communication:** Uses REST API (`requests.post`), sending prompts and parsing LLM responses as plain text.

- **Game Logic:** Modular and easy to expand for online play, more bots, or richer mechanics.

- **Performance:** Excellent on M1 MacBook Pro; actual performance depends on LLM and hardware.

* **Frontend:** The UI is built entirely with the **Kivy** framework. The layout is defined declaratively in `.kv` files (`home_screen.kv`, `settings_screen.kv`), and the logic is handled in corresponding Python files.
* 
* **Game Logic:**
    * `game_board.py`: The main widget that manages the game loop, bots, bullets, and drawing.
    * `bot.py`: Defines the `Bot` class, which handles state, LLM interaction, and command execution.
    * `bullet.py`: Defines the `Bullet` class, managing its movement and collision detection logic.
    * 
* **State Management & History:** The `HistoryManager` class (`history_manager.py`) uses dataclasses to create a structured record of every game, round, and turn, which can be serialized to JSON.
* 
* **Normalized Coordinates:** The `NormalizedCanvas` class (`normalized_canvas.py`) is a clever context manager that allows drawing on the game board using a 0-to-1 coordinate system, making the graphics resolution-independent.

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


## Legal
### Licence
### Disclaimers and more




