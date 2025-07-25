
"""
Data Structure for a Bot's Session History

To make the history easy to save as JSON, use a nested dictionary/list structure of basic data types. Each Bot will maintain its own session history. At a high level, the structure can be:

	•	Bot session history (dict):
		•	bot_id: the bot’s ID (int)
		•	games: a list of game entries (each game is a dict)
  
	•	Game entry (dict):
		•	number: game index (e.g. 0 for the first game, 1 for the next, etc.)
		•	total_rounds: total rounds played in this game (filled in when game ends)
		•	turns_per_round: maximum turns per round (from config, for reference)
		•	rounds: a list of round entries (each round is a dict)
  
	•	Round entry (dict):
		•	number: round index within the game
		•	user_prompt: the prompt text the player entered for this round
		•	prompt_augmented: 1 if prompt augmentation is ON, 0 if OFF (from config)
		•	independent_llms: 1 if using separate LLMs per player, 0 if a single LLM (from config)
		•	turns: a list of turn entries (each turn is a dict)
  
	•	Turn entry (dict):
		•	number: turn index within the round (for that bot)
		•	order: 0 if this bot acted first in that turn cycle, or 1 if it acted second
		•	response: the command the bot issued (e.g. “M”, “B”, “C20”, etc.)
		•	before: the bot’s state before executing the command (position, rotation, shield, health)
		•	after: the bot’s state after executing the command

This mirrors the example structure you outlined, and because it’s composed of dictionaries, lists, and primitive types, it can be directly serialized to JSON using Python’s json module.

"""