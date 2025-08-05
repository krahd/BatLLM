 
>
>  ![BatLLM's logo](./images/logo-small.png) **[Readme](README.md) &mdash; [Documentation](DOCUMENTATION.md)  &mdash; [User Guide](USER_GUIDE.md)  &mdash; [Contributing](CONTRIBUTING.md)  &mdash; [FAQ](FAQ.md)  &mdash; [Credits](CREDITS.md)** 
>
> 

## Contributing (Developer Guide)

This document is for developers who want to understand BatLLM’s code structure or extend the game’s functionality. 

> [!note] 
> **BatLLM is very young!** Pull requests, bug reports, documentation, data analyses, and feature suggestions are most welcome! 

## Getting Started 

To **access the codebase, fork the repository on GitHub** and clone it locally.
Create a new branch for your feature or fix.
Make your changes with clear, well-documented code. If adding a new feature, try to write a short section about it for the documentation as well.

Then, **if you would like to contribute to it, submit a pull request** with a clear description of your changes and the problem they solve or the improvement made.
We *will* review the PR, suggest any changes if necessary, and merge it once it’s ready.

Please open an issue if you find a bug or have a feature request. Even if you’re not coding it yourself, ideas and feedback are extremely helpful.

When contributing, ensure that any new dependencies are necessary and cross-platform. Also, test on multiple platforms if possible, or at least alert us if a change might affect Windows/Mac/Linux differently.


## Technical Notes
  
- **Arena Rendering:** We have extended Kivy's Canvas to create `NormalizedCanvas` in which all positions are floats from 0.0 (top/left) to 1.0 (bottom/right), making the graphics resolution-independent.

- **LLM Communication:** Uses REST API (`requests.post`), sending prompts and parsing LLM responses as plain text.

- **Game Logic:** Modular and easy to expand for online play, more bots, or richer mechanics.

- **Performance:** Excellent on M1 MacBook Pro; actual performance depends on LLM and hardware.

* **Frontend:** The UI is built entirely with the **Kivy** framework. The layout is defined declaratively in `.kv` files (`home_screen.kv`, `settings_screen.kv`), and the logic is handled in corresponding Python files.

* **Game Logic:**
    * `game_board.py`: The main widget that manages the game loop, bots, bullets, and drawing.
    * `bot.py`: Defines the `Bot` class, which handles state, LLM interaction, and command execution.
    * `bullet.py`: Defines the `Bullet` class, managing its movement and collision detection logic.
    
* **State History:** The `HistoryManager` class (`history_manager.py`) uses dataclasses to create a structured record of every game, round, and turn, which can be serialized to JSON.

* **Architecture:** The game is built using a Model-View-Controller-like separation. The **view** (UI) is done in Kivy with a `ScreenManager`. The main game screen (`HomeScreen`) contains the interactive elements (prompt input boxes, prompt history, output log, etc.) and the `GameBoardWidget` where the arena and bots are drawn. The **model** includes the `Bot` class (tracking state and handling LLM interaction) and the simple physics for bullets. The **controller** logic is primarily in `GameBoardWidget` (managing turns, rounds, and coordinating between UI events and bot actions).

* **Arena Rendering:** The game uses a custom `NormalizedCanvas` context, meaning all coordinates for drawing are in the range 0.0–1.0 (where (0,0) corresponds to the top-left of the arena and (1,1) the bottom-right). This makes it easy to think about positions without worrying about pixels or aspect ratio. The arena is drawn as a square within the window with some padding. Bot coordinates (`x`, `y`) are floats in \[0,1], and a bot’s size (`diameter`) is also a fraction of the arena size.

* **Bot Representation:** Bots are drawn as circles with a line indicating facing direction. Each bot also has a small on-screen text box attached that shows its current `x`, `y`, `rot` (rotation angle in degrees), shield status, and health. This updates in real time so players and observers can see the state without parsing logs.

* **LLM Communication:** Communication with the LLMs is done via HTTP requests. The `Bot` class uses `kivy.network.urlrequest.UrlRequest` to send a POST to the configured endpoint with a JSON payload. For Ollama, the payload looks like:

  ```json
  { "model": "llama3.2:latest", "prompt": "<PROMPT_TEXT>", "stream": false }
  ```

  The LLM server is expected to return a JSON response containing a field (for Ollama it's `"response"`) with the model’s output. The game will take this output and parse it for a command as described above. Non-blocking requests are used, so the game doesn’t freeze while waiting for the LLM. Each bot’s LLM call runs in parallel. A callback updates the game state when the response comes in.

* **LLM Response Parsing:** The LLM’s raw text response can technically be anything, but BatLLM expects it to be a command string. The code is **defensive**: if the response is a list (some APIs return an array of choices), it takes the first element; if it’s a string, it uses it as-is. It then looks at the first character to determine the action. If the response doesn’t correspond to a valid command (or is empty), that bot simply does nothing for that turn. This design encourages players to craft prompts that yield a clear command. The prompt augmentation instructions explicitly tell the LLM to output a valid command in the correct format.

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


* **Extensibility:** The code is structured to allow modifications. For example, you can add new commands by extending the `match` in `Bot._on_llm_response` and adding a corresponding method in Bot or GameBoard. You could add new screens (like a main menu or a post-game stats screen) via Kivy’s ScreenManager. The separation of concerns means, for instance, you could swap out the LLM communication part (to use an OpenAI API or another library) by modifying the Bot class without touching the game logic or UI. We encourage experimentation—BatLLM is as much a sandbox for AI interaction as it is a game.


## Important Files

* **`home_screen.py`** is the main game UI screen containing prompt inputs, history, etc., and the game board widget. It handles most of the user interaction.
* **`game_board.py`**  `GameBoardWidget` and implements the game world (board), mechanics, logic, and rendering.
* **`bot.py`**  `Bot` class which models the game's bots. It stores the bot's state, implements its behaviours, while also taking care of the interaction with the LLM and rendering the bot on the game canvas.
* **`bullet.py`** defines the `Bullet` class, which handles bullet movement and collision logic. A bullet is not a Kivy widget but a logical object; drawing the bullet is handled within the GameBoard’s canvas.
* **`history_manager.py`** defines the HistoryManager which keeps track of what happens and is able to save this information as a JSON file. 

## Coding Style 

* The code is mostly straightforward, using Python 3.10+ pattern matching (`match/case`) for command parsing which is nice.
* Use American english for the code and your preferred English flavour for documentation, comments, etc.
* Spacing and naming: it uses snake\_case for functions and variables (PEP8 style). Some parts (like some print debugging statements) can be cleaned up or removed.
* Comments: There are several TODOs in code. Please feel free to address these if you want.
* Although insofar the code has only been run on MacOS, please keep cross-platform in mind: avoid using OS-specific file paths. For example, use `Path` (as seen in app\_config using pathlib).
* When in doubt, always choose the more inclusive option.

## Potential Roadmap Ideas 

* Extending Game Mechanics: bot actions, explore different world sizes. 
* Autonomous behaviour (NPCs, world elements).
* Adding new methods of prompt augmentation.
* UI improvement (graphics, interaction, etc.).
* Network-based multiplayer 
* Augment the number of simultaneous players.
* Analyse the saved histories, search for patterns and insights.
* Team battles.
* Single-Player Mode against AI-controlled LLMs or against stored prompts.
* Shared prompt storage, ranking, and sharing. 
* Scalability and Testing.

## License

This project is licensed under the MIT License. See the [LICENSE](/LICENSE) file for details. This means you’re free to use, modify, and distribute this software as long as you include the license notice. We hope you’ll contribute back any improvements!

*More coming soon...*



