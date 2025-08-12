  
>
>  ![BatLLM's logo](./images/logo-small.png) **[Readme](README.md) &mdash; [Documentation](DOCUMENTATION.md)  &mdash; [User Guide](USER_GUIDE.md)  &mdash; [Contributing](CONTRIBUTING.md)  &mdash; [FAQ](FAQ.md)  &mdash; [Credits](CREDITS.md)** 
>
>

# User Guide

## Mini Demo

The screen recording below shows the basic interaction flow: players input a prompt and submit it to their bot. When both players have done so a new round begins.

Prompts can be loaded and saved to the filesystem (they are jsut text files), or can be fetched from the bot's history of submitted prompts. 

To see actual I/O with the LLM you can open the History Screen, and to change the game's parameter you can use the Settings Screen.

![Demo Gif](./screenshots/quick_demo.gif)

## Game Flow and Rules

A match consists of one or more rounds; each round consists of several turns. The game flow is as follows:

1. **Before the Round:**
   Both players are prompted to enter a new prompt for their bots. Once both players have submitted their prompts, the round begins. 

2. **During Each Turn:**
   * At the start of each turn, the game randomly selects which player’s bot will act first for that turn (this random order is determined once per round).
   * The first bot’s prompt (augmented or raw, depending on settings) is sent to its LLM using Kivy's Clock to run it non blockingly with respect to the game renderiing loop. The LLM returns a command which is immediately executed by the bot in the game world. The game state is updated and rendered on the screen.
   * If the command was to fire, the entire lifespan of the bullet is part of the turn execution. That is, the bot only finishes its turn when the bullet resolves into a hit or not. The bullet travels until it either hits the other bot or goes out of bounds. A bullet that hits a bot outside its shield reduces the target bot's health by BULLET_DAMAGE. The damage is also part of the turn, which means that the may finish abruptly. If it misses, the turn continues. The opponent bot cannot act or move until the other bot has finished.
   * Next, the second bot’s prompt is sent to its LLM, and that bot then executes its command for the turn, updating the state and UI accordingly (unless the round already ended due to the first bot destroying the opponent).
   * This completes one turn (both bots have acted once).

3. **End of Round / Match:**

   * If a bot’s health reaches zero at any point, the match ends immediately. There is no respawning; a destroyed bot means the game is over.
   * If neither bot is destroyed and the predefined number of turns in the round elapses (`TURNS_PER_ROUND` in settings), the round ends automatically. A popup will show the round results (e.g., remaining health of each bot). If the game is set to multiple rounds (`TOTAL_ROUNDS`), and both bots are still alive, the next round can begin. Players can then input new prompts (or reuse previous ones) for the next round.

Between rounds, players have the opportunity to adjust their strategy by writing new prompts. This is a key part of BatLLM’s educational value: you can analyze what the LLM did in the prior round and modify your prompt to guide it differently in the next round.

## Bot Commands Reference

| Code   | Action                                                                    | Example  |
|--------|---------------------------------------------------------------------------|----------|
| `C{angle}`   | **Rotate clockwise** by `angle` degrees.                                      | `C90`   | 
| `Aangle`   | **Rotate anticlockwise** by `angle` degrees.                                 | `A45`   | 
| `M`    | **Move forward** by one step (`STEP_LENGTH`).                                   | `M`     | 
| `S1`   | **Raise shield**. Remains up until changed.                               | `S1`    |
| `S0`   | **Lower shield**. Remains down until changed.                             | `S0`    |
| `S`    | **Toggle shield**: raises if down, lowers if up.                          | `S`     |
| `B`    | **Shoot**: If its shield is lowered, fires fires one bullet.             | `B`     |
*Any other output from the LLM is interpreted as 'do nothing' this turn.*

## Modes and Variations

<!--#TODO rewrite --> 

* **Standard Mode:** Each player writes a prompt at the beginning of a round; both prompts are sent to their respective LLMs each turn of that round.
* **Prompt Augmentation:** Optionally, the game augments the player's prompt with structured game state info (see [Prompt Augmentation](#prompt-augmentation)).
* **LLM Assignment:**

  * *Separate LLMs:* The context of each player only their prompt/response cycles and the gamedata.
  * *Single LLM:* The context is the same for both bots and includes all the prompt/responses of both bots. This introduces pontential malicious prompting where players try to disrupt each others prompts with their own.

**Note:** There are **no** NPC Bots. BatLLM is strictly AI mediated human-vs-human gaming. all gameplay decisions are made by human-written prompts, then carried out by LLMs. 


## Configuration
BatLLM can be configured via a YAML file (`configs/config.yaml`). Command line parameters will be introduced at some point.

> [!IMPORTANT]
> Avoid modifying this file while BatLLM is running. 
> 

**YAML configuration file:** *The current configuration file may have slightly different default values or keys; the code below is illustrative.*
Please see the the repository’s [/src/configs/config.yaml](../src/configs/config.yaml) file for the exact format.

```yaml
data:
  saved_sessions_folder: saved_sessions
game:
  bot_diameter: 0.1
  bullet_damage: 10
  independent_models: true
  initial_health: 42
  prompt_augmentation: false
  shield_initial_state: true
  shield_size: 35 
  step_length: 0.02
  total_rounds: 3
  turns_per_round: 20
llm:
  augmentation_header_file: assets/prompts/augmentation_header_1.txt
  path: /api/generate
  port: 5000
  url: http://localhost
ui:
  font_size: 16
  frame_rate: 60
  primary_color: '#0b0b0b'
  title: BatLLM

```

Configuration Options include:

- **data:**
	- **saved_sessions_folder** is the default folder for saved games.
- **game:**
	- **shield_size:** how long the shield extends *from the bot's front **in each direction**.*
	- **step_length:** how long a single M command moves the bot.
	- **total_rounds:** in a game
    - **ullet_damage:** 
  **llm:**
	- **augmentation_header_file:** is a text file that is inserted at the top of *every  prompt* when playing with augmentation on.
	- **path:** of the LLM endpoint 
	- **port:** of the LLM endpoint 
	- **url** of the LLM endpoint (url/path:port)
- **ui:**
	- **font_size:** 16 
	- **primary_color:** the colour for the GUIs text.
	


**Command-line Arguments are not currently implemented**, but future versions may allow overriding these settings via command-line options for convenience and experimentation.

Avoid modifying this file while BatLLM is running.

*More coming soon...*




