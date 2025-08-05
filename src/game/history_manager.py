import json
from datetime import datetime
from configs.app_config import config

class HistoryManager:
	def __init__(self):
		"""Initialize a new HistoryManager with no active game."""
		self.games = []                  # List of games played in this session (BotLLM run)
		self.current_game = None         # Dictionary for the current game's history
		self.current_round = None        # Dictionary for the current round's history
		self.current_turn = None         # Dictionary for the current turn's history

	def _now_iso(self):
		"""Get current timestamp string in ISO 8601 format."""
		return datetime.now().isoformat()  # e.g. "2025-07-25T21:05:30.123456"


	def start_game(self, game_board):
		"""
		Start a new game. Initialize the game log with start time and initial bot states.
		`game_board` is the BoardGameWidget
		"""
		
		# If a game was in progress without proper ending, finalize it (to keep data consistent)
		if self.current_game and 'end_time' not in self.current_game:
			# Finalize previous session if not already ended
			self.end_game(game_board, force=True)
		
		# Create new game entry
		self.current_game = {
			"game_id": len(self.games) + 1,
			"start_time": self._now_iso(),
			"initial_state": {},
			"rounds": [],
			"winner": None,  # Will be set at game end
		}
		
		# Record initial state of all bots at game start  TODO probably remove this
		bots_state = self._get_bots_state(game_board)
		self.current_game["initial_state"] = bots_state
		
		# We could store static info or config data here
		
		# Append this session to sessions list
		self.games.append(self.current_game)
		
		# Reset current round/turn since new game
		self.current_round = None
		self.current_turn = None




	def end_game(self, game, force=False):
		"""
		End the current game. This can be called at any time (e.g., normal game end or aborted mid-round).
		It finalizes any ongoing round/turn and records the end time and final outcome.
		The parameter `force` is used internally to finalize a game without double-calling end_game recursively.
		"""
		
		if not self.current_game:
			return  # No active session to end

		# If a turn is in progress (start_turn called without end_turn), handle it
		if self.current_turn and "post_state" not in self.current_turn:
			
			# Take a final snapshot for the turn (likely nothing changed if aborted mid-turn)
			self.current_turn["end_time"] = self._now_iso()
						
			self.current_turn["post_state"] = self._get_bots_state(game)
			
			# (We could mark this turn as aborted or incomplete if needed)
			self.current_turn = None

		# If a round is in progress and not yet ended, end it now
		if self.current_round and "end_time" not in self.current_round:
			# Mark round end time
			self.current_round["end_time"] = self._now_iso()                                    
			self.current_round = None

		# Mark session end time
		self.current_game["end_time"] = self._now_iso()
		self.current_game["winner"] = self._determine_winner(game)
				
		# After ending game, clear current_session (still stored in self.sessions list)
		self.current_game = None
		self.current_round = None
		self.current_turn = None


	def start_round(self, game):
		"""
		Start a new round within the current session. Should be called at the beginning of each round.
		Records the round start and the initial state at this point.

		Args:
			game (_type_): _description_
		"""
		
		if not self.current_game:
			# If game not started, start a game automatically (or raise an error)
			self.start_game(game)
		
		
		# Close any previous round if it wasn't properly closed (should not normally happen if end_round was called)
		if self.current_round and 'end_time' not in self.current_round:
			# End the previous round automatically before starting new one
			self.end_round(game)
			
		# Create new round entry
		round_number = len(self.current_game["rounds"]) + 1
		
		self.current_round = {
			"round": round_number,
			"start_time": self._now_iso(),
			"initial_state": {},  # TODO ponder if we want this            
			"turns": []
		}
		
		# Snapshot state at round start     
		self.current_round["initial_state"] = self._get_bots_state(game)
		
		# Append to session's rounds list
		self.current_game["rounds"].append(self.current_round)
		
		# Reset current turn
		self.current_turn = None



	def end_round(self, game):
		"""
		End the current round. Records the end time and round winner.
		"""
		
		if not self.current_round:
			return  # No active round to end
		
		# If a turn is in progress within this round, end that turn first
		if self.current_turn and "post_state" not in self.current_turn:
			self.end_turn(game)
			
		# Mark round end time
		self.current_round["end_time"] = self._now_iso()
		
		
		# After ending the round, clear current_round (still stored in session rounds list)
		self.current_round = None
		self.current_turn = None



	def start_turn(self, game):
		"""
		Start a new turn within the current round. Called at the beginning of a turn.
		Records the pre-turn state and which bot is acting (if available).
		"""

		if not self.current_round:
			# If there's no active round we start a new one
			self.start_round(game)
			
		# Create new turn entry
		turn_number = len(self.current_round["turns"]) + 1
		
		self.current_turn = {
			"turn": turn_number,
			"start_time": self._now_iso(),   #     TODO check this
			"pre_state": {},
		}
			   
			
		# Snapshot pre-turn state of all bots
		self.current_turn["pre_state"] = self._get_bots_state(game)

		# Add this turn to the current round's turn list
		self.current_round["turns"].append(self.current_turn)



	def end_turn(self, game, action_description=None):
		"""
		End the current turn. Called after the turn's action is resolved.
		Records the post-turn state and (optionally) the action description.
		"""
		if not self.current_turn:
			return  # No active turn to end (or already ended)

		
		# Record end time for the turn     TODO probably remove this
		self.current_turn["end_time"] = self._now_iso()

		
		# Snapshot post-turn state of all bots
		self.current_turn["post_state"] = self._get_bots_state(game)

			
		# Clear current_turn (it remains in the turns list of the round)
		self.current_turn = None

		

	def _get_bots_state(self, game):
		"""
		Helper method to get a snapshot of all relevant bot data from the game.
		Returns a dictionary of bot states (keyed by bot name or id).
		"""
		state = {}
		# Determine how bots are stored in the game object.
		# This implementation assumes game has either a list/iterable of bots or attributes bot1, bot2, etc.
		
		bots = []
		
		if hasattr(game, "bots"):
			
			# If game.bots exists (possibly a list or dict of bots)
			try:
				# Try to get iterable of bots
				bots_iter = list(game.bots) if not isinstance(game.bots, dict) else list(game.bots.values())
				
			except TypeError:
				# If game.bots is not directly iterable (e.g., a single object), make it a single-element list
				bots_iter = [game.bots]
				
			bots = bots_iter
			
		else:
			
			# Fallback: check common attribute names for two players scenario
			if hasattr(game, "bot1"):
				bots.append(game.bot1)
				
			if hasattr(game, "bot2"):
				bots.append(game.bot2)
				
		# Iterate over collected bot objects and record their state
		for bot in bots:
			if not bot:
				continue
			
			# Determine a key to identify the bot (prefer name if available)
			bot_id = bot.id
				  
			# Gather relevant attributes
			bot_info = {}            
			bot_info["id"] = bot_id
			bot_info["health"] = bot.health
			bot_info["x"] = bot.x
			bot_info["y"] = bot.y   
			bot_info["rot"] = bot.rot
			bot_info["shield"] = bot.shield
			bot_info["prompt"] = bot.get_current_prompt()
			bot_info["llm_response"] = bot.last_llm_response 
			
			state[bot_id] = bot_info
			
		return state



	def _determine_winner(self, game):
		"""
		Determine which bot is the winner given the current game state.
		This checks the bots' alive status or health to see if one is defeated.
		Returns the winner's name, or None if no clear winner.
		"""
		bots_state = self._get_bots_state(game)
		
		alive_bots = [id for id, info in bots_state.items() if info["health"] > 0]
		
		if len(alive_bots) == 1:
			# Only one bot alive -> that bot is the winner
			return alive_bots[0]
		
		else:
			# Either no bots alive (draw or both died) or more than one alive (no winner yet)
			return None


	def save_session(self, filepath):
		"""
		Save the entire session history to a JSON file.
		This will include all games played in this session.
		"""
		
		with open(filepath, 'w', encoding="utf-8") as f:  # JSON spec requires UTF-8 support by decoders. 
			json.dump(self.games, f, indent=4, ensure_ascii = False)
		
	def to_json(self):
		"""
		Get the full history as a JSON string.        
		"""        
		return json.dumps(self.games, indent=4)


	def to_text(self):
		"""
		Get the full history in a human-readable indented text format (key: value style).
		Returns a multi-line string.        
		"""
		lines = []
		game_num = 1
		for game in self.games:            
			total_rounds = len(game.get("rounds", []))
			
			# Session header
			lines.append(f"Game {game_num}:")
			game_num += 1
			
			# Game-level details
			if "start_time" in game:
				lines.append(f"    Start Time: {game['start_time']}")
			if "end_time" in game:
				lines.append(f"    End Time: {game['end_time']}")
				
			# Initial state of bots at game start
			if "initial_state" in game:
				init_state = game["initial_state"]
				bot_states = []
				
				for bot_id, info in init_state.items():
					# Example: "BotA (HP=100)"
					hp = info.get("health")
					
					if hp is not None:
						bot_states.append(f"{bot_id} (HP={hp})")
					else:
						bot_states.append(f"{bot_id}")
						
				if bot_states:
					lines.append(f"    Bots: " + ", ".join(bot_states))
					
			# Rounds
			for round_entry in game.get("rounds", []):
				rnd = round_entry.get("round")
				lines.append(f"    Round {rnd}:")
				
				if "start_time" in round_entry:
					lines.append(f"        Start: {round_entry['start_time']}")
					
				# If initial round state is recorded, we could output it (but often it's same as previous end)
				# We'll focus on turn-by-turn details below.
				
				# Turns:
				for turn in round_entry.get("turns", []):
					tnum = turn.get("turn")
					
					# Turn header line
					lines.append(f"        Turn {tnum}:")
					
					# For each bot, show HP change (or other changes) from pre to post # TODO change this, store pre data and post data, not delta
					pre = turn.get("pre_state", {})
					post = turn.get("post_state", {})
					
					for bot_id, pre_info in pre.items():
						post_info = post.get(bot_id, {})
						
						# Health change example
						if "health" in pre_info or "health" in post_info:
							pre_hp = pre_info.get("health")
							post_hp = post_info.get("health")
							
							if pre_hp is None: 
								# If pre_hp missing, assume 0 or unknown
								pre_hp = pre_hp if pre_hp is not None else "N/A"
								
							if post_hp is None:
								post_hp = post_hp if post_hp is not None else "N/A"
								
							if pre_hp == post_hp or post_hp is None or pre_hp is None:
								# No change (or unknown)
								lines.append(f"            {bot_id} HP: {pre_hp}")
								
							else:
								change = post_hp - pre_hp if isinstance(pre_hp, (int, float)) and isinstance(post_hp, (int, float)) else None
								
								if change is None:
									# If not numeric or can't compute change, just show arrow
									lines.append(f"            {bot_id} HP: {pre_hp} -> {post_hp}")
								else:
									# Show change with sign
									sign = "+" if change > 0 else ""
									lines.append(f"            {bot_id} HP: {pre_hp} -> {post_hp} ({sign}{change})")
									
						# we can show how other attributes changed as well. 
						
					# If a bot died during this turn (alive became false), mark it
					for bot_id, pre_info in pre.items():
						pre_alive = pre_info.get("health", 0) > 0
						post_alive = post.get(bot_id, {}).get("health", 0) > 0
						
						if pre_alive and post_alive is False:  # was alive, now not
							lines.append(f"            [{bot_id} died]")
							
				# Round end and winner
				if "end_time" in round_entry:
					lines.append(f"        End: {round_entry['end_time']}")                                 
						
			# Game winner
			if "winner" in game:
				win = game["winner"]
				
				lines.append(f"    Winner: {win if win else '(none)'}")
				
			# Blank line between sessions if multiple
			lines.append("")
			
		return "\n".join(lines)