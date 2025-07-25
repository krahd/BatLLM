# HistoryManager for BatLLM Game

## Overview

The HistoryManager is a Python class designed to log an entire play session of the BatLLM game. It records multiple games per session, capturing all rounds and turns for both bots in a structured way. This provides a complete history of gameplay that can be saved to a JSON file for analysis or replay. According to the BatLLM game flow, a match consists of rounds, and each round consists of turns ￼. In each round, both players enter their prompts, and then the game executes two turns (one per bot) in a random order ￼. The HistoryManager leverages this structure to organize the data hierarchically by session → games → rounds → turns.

##Session Data Structure

The HistoryManager maintains a session with metadata and a nested structure of games, rounds, and turns. All data is stored in plain Python data structures (dicts and lists) or lightweight data classes, ensuring easy conversion to JSON. The hierarchy is as follows:
- Session:
    - session_start – Timestamp when the session started (e.g. ISO 8601 string).
    - session_end – Timestamp when the session ended (set when saving).
    - games – List of game records (one entry per game played in this session).
- Game:
    - game_number – Sequential game index (1, 2, 3, …).
    - total_rounds – Total number of rounds played in this game.
    - turns_per_round – Number of turns per round (for two bots this is 2).
    - rounds – List of round records for this game.
- Round:
    - round_number – Sequential round index within the game (1, 2, 3, …).
    - prompts – The prompts that players entered for this round. This can be stored as a list or dict of two strings (one per bot). Each prompt may have been augmented with game state if augmentation is enabled. BatLLM’s prompt augmentation feature, when enabled, prepends the player’s prompt with structured game state info ￼. When disabled, only the raw prompt is sent ￼.
    - augmented – Boolean flag indicating if prompt augmentation was used for this round (this is typically a game-wide setting ￼, so it will be the same for all rounds in a game).
    - independent_llms – Boolean flag indicating if each player’s prompt was handled by separate LLM instances or a single shared LLM. BatLLM supports two separate LLMs (one per player) or a single shared model ￼; this setting is recorded here for context.
    - turns – List of turn records for this round.
- Turn:
    - turn_number – Sequential turn index within the round (usually 1 or 2 in a two-bot game).
    - order – Which bot acted in this turn (0 for bot1’s turn, 1 for bot2’s turn). The game decides a random first player each round ￼, and turns alternate accordingly.
    - llm_response – The raw response string returned by the LLM for this turn. This is essentially the command the LLM produced based on the bot’s prompt and the game state ￼.
    - pre_state – The state of the acting bot before executing the LLM’s command. This is a dictionary containing at least the bot’s x (x-coordinate), y (y-coordinate), rot (rotation/angle), shield (shield status up/down), and health (hit points) values.
    - post_state – The state of the same bot after the turn, i.e. after applying the command. It has the same structure as pre_state, reflecting any changes (position move, rotation, shield toggle, health change, etc.) resulting from the action.

This nested structure cleanly separates data by game, round, and turn, making it easy to inspect or analyze specific parts of the session (e.g., all actions in a particular round). All parts of the structure are composed of basic data types (ints, strings, bools, dicts, lists), which are naturally serializable to JSON.

## Example JSON Structure

Below is a simplified example of how the session data might look as JSON (with one game of two rounds, each round having two turns)

```json
{
  "session_start": "2025-07-25T13:10:56.123456",
  "session_end": "2025-07-25T13:30:00.654321",
  "games": [
    {
      "game_number": 1,
      "total_rounds": 2,
      "turns_per_round": 2,
      "rounds": [
        {
          "round_number": 1,
          "prompts": ["Try to dodge the enemy.", "Aim and shoot at player1"], 
          "augmented": true,
          "independent_llms": false,
          "turns": [
            {
              "turn_number": 1,
              "order": 1,
              "llm_response": "M", 
              "pre_state": {"x": 0.5, "y": 0.2, "rot": 90, "shield": 0, "health": 10},
              "post_state": {"x": 0.5, "y": 0.3, "rot": 90, "shield": 0, "health": 10}
            },
            {
              "turn_number": 2,
              "order": 0,
              "llm_response": "B", 
              "pre_state": {"x": 0.7, "y": 0.8, "rot": 270, "shield": 1, "health": 8},
              "post_state": {"x": 0.7, "y": 0.8, "rot": 270, "shield": 1, "health": 8}
            }
          ]
        },
        {
          "round_number": 2,
          "prompts": ["Close in on the enemy.", "Fall back and raise shield"], 
          "augmented": true,
          "independent_llms": false,
          "turns": [
            {
              "turn_number": 1,
              "order": 0,
              "llm_response": "M", 
              "pre_state": {"x": 0.5, "y": 0.3, "rot": 90, "shield": 0, "health": 10},
              "post_state": {"x": 0.55, "y": 0.3, "rot": 90, "shield": 0, "health": 10}
            },
            {
              "turn_number": 2,
              "order": 1,
              "llm_response": "S1", 
              "pre_state": {"x": 0.7, "y": 0.8, "rot": 270, "shield": 1, "health": 8},
              "post_state": {"x": 0.7, "y": 0.8, "rot": 270, "shield": 1, "health": 8}
            }
          ]
        }
      ]
    }
  ]
}
```


