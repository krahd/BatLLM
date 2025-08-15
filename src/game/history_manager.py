import json
from datetime import datetime

from configs.app_config import config
from game.bot import Bot

"""
Events
    start_game
    start_round
    start_turn
    end_turn
    end_round
    end_game gb
"""


class HistoryManager:
    """
    HistoryManager

    A class to manage and record the complete history of games, rounds, turns, and chat interactions
    between bots and an LLM in a session. The HistoryManager acts as the single source of truth for
    all game-related events, including state snapshots, chat messages, parsed commands, and outcomes.

    Features:
    - Tracks multiple games within a session, each with rounds and turns.
    - Records detailed state snapshots of all bots at key points (game start, round start, pre/post turn).
    - Manages chat-style interactions for each turn, storing messages with bot IDs, roles, and content.
    - Supports recording parsed commands and post-action states for each bot per turn.
    - Provides methods to reconstruct chat history, both shared and per-bot.
    - Determines game winners based on bot health.
    - Exports session history in JSON, human-readable text, and compact UI-friendly summaries.

    Usage:
    - Instantiate once per session/run.
    - Call start_game(), start_round(), start_turn(), and their corresponding end_* methods at appropriate times.
    - Use record_message(), record_parsed_command(), and record_post_action_state() to log bot-LLM interactions.
    # TODO this will changes
    - Retrieve history for display, debugging, or saving via to_json(), to_text(), to_compact_text(), etc.

    Attributes:
        games (list): List of all games played in the session.
        current_game (dict or None): The currently active game's history.
        current_round (dict or None): The currently active round's history.
        current_turn (dict or None): The currently active turn's history.

    Methods:
        start_game(game_board): Begin a new game and initialize its history.
        end_game(game, force=False): Finalize the current game, recording end time and winner.
        start_round(game, first_round=False): Begin a new round within the current game.
        end_round(game): Finalize the current round.
        start_turn(game): Begin a new turn within the current round.
        end_turn(game): Finalize the current turn.

        record_message(bot_id, role, content): Record a chat message for the current turn.
        record_parsed_command(bot_id, command): Record the parsed command for a bot in the current turn.
        record_post_action_state(bot_id, game): Record a bot's state after its action in the current turn.

        get_chat_history(bot_id=None, shared=True): Retrieve chat history for the current game.

        save_session(filepath): Save the session history to a JSON file.

        to_json(): Get the full session history as a JSON string.
        to_text(): Get the full session history as a human-readable string.
        to_compact_text(): Get a compact, UI-friendly summary of the session history.
        to_compact_text_for_bot(bot_id): Get a compact, per-bot summary of the session history.
    """



    def __init__(self):
        """Initialize a new HistoryManager with no active game."""
        self.games = []  # List of games played in this session (BotLLM run)
        self.current_game = None  # Dictionary for the current game's history
        self.current_round = None  # Dictionary for the current round's history
        self.current_turn = None  # Dictionary for the current turn's history


        # TODO THIS will change
        # When recording chat-style interactions with the LLM we attach a list
        # of messages to each turn. Each message is a dictionary with keys
        # ``bot_id`` (int), ``role`` (str) and ``content`` (str). The HistoryManager
        # is the single source of truth for all chat exchanges; the game code
        # accesses this data to reconstruct the conversation for either shared
        # context (both bots combined) or independent context (per bot).

    def _now_iso(self):
        """Get current timestamp string in ISO 8601 format."""
        return datetime.now().isoformat()  # e.g. "2025-07-25T21:05:30.123456"



    def start_game(self, game_board):
        """
        Start a new game. Initialize the game log with start time and initial bot states.
        `game_board` is the BoardGameWidget
        """

        # If a game was in progress without proper ending, finalize it (to keep data consistent)
        if self.current_game and "end_time" not in self.current_game:
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
        # bots_state = self._get_bots_state(game_board)
        # self.current_game["initial_state"] = bots_state

        # Append this session to sessions list
        self.games.append(self.current_game)

        # Reset current round/turn since new game
        # TODO create a new round at game start???

        self.current_round = None
        self.current_turn = None



    def end_game(self, game):
        """
        End the current game. This can be called at any time (e.g., normal game end or aborted mid-round).
        It finalizes any ongoing round/turn and records the end time and final outcome.
        """

        if not self.current_game:
            raise ValueError(
                "Cannot end a game that was never started. Call start_game first."
            )

        # If a turn is in progress (start_turn called without end_turn), handle it
        if self.current_turn and "post_state" not in self.current_turn:

            # Take a final snapshot for the turn (likely nothing changed if aborted mid-turn)
            self.current_turn["end_time"] = self._now_iso()
            self.current_turn["post_state"] = self._get_bots_state(game)
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
        Start a new round within the current game.

        Args:
            game: The current game object (e.g., BoardGameWidget).

        Raises:
            ValueError: If there is no active game or a round is already in progress.
        """

        if not self.current_game:
            raise ValueError(
                "Cannot start a round without an active game. Call start_game first."
            )


        # Create the new round entry
        round_number = len(self.current_game["rounds"]) + 1

        self.current_round = {
            "round": round_number,
            "start_time": self._now_iso(),
            "initial_state": {},
            "prompts": [],
            "turns": [],
        }

        # Snapshot the state at round start
        self.current_round["initial_state"] = self._get_bots_state(game)

        # Append the round to the game's list of rounds
        self.current_game["rounds"].append(self.current_round)

        # TODO  how add the prompts to the new round
        # self.current_round["prompts"] = []


        # Reset current turn
        self.current_turn = None



    def end_round(self):
        """
        End the current round. Records the end time and round winner.
        """

        # if there's no active round, raise an error
        if not self.current_round:
            if not self.current_round:
                raise ValueError(
                    "There is no active round to end. Call start_round first."
                )

        # If a turn is in progress within this round, raise an error
        if self.current_turn and "post_state" not in self.current_turn:
            if not self.current_round:
                raise ValueError(
                    "Cannot end a round mid turn. Call end_turn first")

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
            # If there's no active round we throw an exception
            raise ValueError(
                "Cannot start a turn without an active round. Call start_round first."
            )

        # Create a new turn entry
        turn_number = len(self.current_round["turns"]) + 1

        self.current_turn = {
            "turn": turn_number,
            "start_time": self._now_iso(),
            "pre_state": {},
            "llm_response": {},
            "post_state": {},
        }

        # Snapshot pre-turn state of all bots
        self.current_turn["pre_state"] = self._get_bots_state(game)

        # Add this turn to the current round's turn list
        self.current_round["turns"].append(self.current_turn)



    def end_turn(self, game):
        """
        End the current turn. Called after the turn's action is resolved.
        Records the post-turn state and clears the current turn.
        """
        if not self.current_turn:
            # If there's no active turn we throw an exception
            raise ValueError(
                "Cannot end a non-existent turn. Call start_turn first.")

        # Record the turn's end time
        self.current_turn["end_time"] = self._now_iso()


        # Snapshot post-turn state of all bots
        self.current_turn["post_state"] = self._get_bots_state(game)

        # Clear current_turn (it remains in the turns list of the round)
        self.current_turn = None


    def add_play(self, bot: Bot):
        """
        Record a play for the bot in the current turn.
        This is a convenience method to record the bot's last command and response.
        """


        if not self.current_turn:
            # If there's no active turn, raise an error
            raise ValueError(
                "Cannot record a play without an active turn. Call start_turn first."
            )

        if self.current_turn["plays"] is None or not isinstance(self.current_turn["plays"], list) or len(self.current_turn["plays"]) == 0:
            # Initialize plays list if it doesn't exist
            plays = []

        play = {}
        play["bot_id"] = bot.id
        play["llm_response"] = bot.last_llm_response
        play["cmd"] = bot.last_cmd if bot.last_cmd else "ERR"
        self.current_turn.setdefault("plays", []).append(play)





    # TODO rename to something like get llm responses
    def get_chat_history(self, bot_id: int | None = None, shared: bool = True) -> list[dict[str, str]]:
        """Reconstruct the chat history for the current game.
        """
        history: list[dict[str, str]] = []
        # If there is no active game, return empty history.
        if not self.current_game:
            return history

        # Iterate over all completed rounds and their turns.
        rounds = self.current_game.get("rounds", [])
        for rnd in rounds:
            for turn in rnd.get("turns", []):

                # TODO change this to use the res cmd and state
                for msg in turn.get("messages", []):
                    if shared or bot_id is None:
                        history.append(
                           {"role": msg["role"], "content": msg["content"]})
                            else:
                            # Only include messages from the specified bot.
                            if msg.get("bot_id") == bot_id:
                            history.append(
                               {"role": msg["role"], "content": msg["content"]})

                                # Also include any messages recorded in the current turn (if it exists).
                                # TODO Change this to use the res cmd and state
                                if self.current_turn and "messages" in self.current_turn:
                                for msg in self.current_turn["messages"]:
                                if shared or bot_id is None:
                                history.append(
                        {"role": msg["role"], "content": msg["content"]})
                        else:
                        if msg.get("bot_id") == bot_id:
                        history.append(
                           {"role": msg["role"], "content": msg["content"]})

                            return history




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
                bots_iter = (
                    list(game.bots)
                    if not isinstance(game.bots, dict)
                    else list(game.bots.values())
                )

                except TypeError:
                # If game.bots is not directly iterable (e.g., a single object), make it a single-element list
                bots_iter = [game.bots]

                bots = bots_iter

                # Iterate over the collected bot objects and record their state
                for bot in bots:
                if not bot:
                continue

                bot_id = bot.id

                # Gather all the bot's relevant attributes
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
        In only one bot is alive, it's the winner. Otherwise, return None.
        """
                bots_state = self._get_bots_state(game)

                alive_bots = [id for id, info in bots_state.items()
                     if info["health"] > 0]

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

        with open(
            filepath, "w", encoding ="utf-8"
        ) as f:  # JSON spec requires UTF-8 support by decoders.
        json.dump(self.games, f, indent=4, ensure_ascii=False)
