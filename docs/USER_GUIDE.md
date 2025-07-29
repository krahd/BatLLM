 
>
>  ![BatLLM's logo](./images/logo-small.png) **[Readme](README.md) &mdash; [Documentation](DOCUMENTATION.md)  &mdash; [User Guide](USER_GUIDE.md)  &mdash; [Contributing](CONTRIBUTING.md)  &mdash; [FAQ](FAQ.md)  &mdash; [Credits](CREDITS.md)** 
>
>
## User Guide

### Configuration

BatLLM can be configured via a YAML file (`configs/config.yaml`) or by modifying constants in the code. 

**Avoid modifying this file while BatLLM is running.**

**YAML configuration file:**
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
  port_base: 5000
  url: http://localhost
ui:
  font_size: 16
  frame_rate: 60
  primary_color: '#0b0b0b'
  title: BatLLM

```

Configuration options include:

- **data:*
	- **saved_sessions_folder** is the default folder for saved games.
- **game:**
	- **bot diameter:** the size of the bot
	- **independent_models:** false uses a single model for both players.
	- **Prompt Augmentation:** on and off
	  shield_initial_state: true
	  **shield_size:** how long the shield extends *from the bot's front **in each direction**.*
	  **step_length:** the M command.
	  **total_rounds:** per game
	  **turns_per_round:** can be changed mid game
**llm:**
  **augmentation_header_file:** is a text file that is inserted at the top of every augmented prompt. 
  **path:** of the LLM's url
  **port_base:** The port of the LLM that player 1's bot uses is port_base + 1. The port of the LLM that player 2's bot uses is port_base + 2. 
  **http://localhost** the url of the LLM
**ui:**
  font_size: 16
  frame_rate: 60
  primary_color: '#0b0b0b'
  title: BatLLM

*The current configuration file may have slightly different default values or keys; the above is illustrative. See the repository’s `configs/config.yaml` for the exact format.*


Command-line Arguments are not currently implemented, but future versions may allow overriding these settings via command-line options for convenience (e.g., `--no-augment` to disable prompt augmentation quickly).

**Avoid modifying this file while BatLLM is running.**

*More coming soon...*




