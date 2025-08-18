import json
from datetime import datetime

from kivy.utils import escape_markup

from configs.app_config import config
from game.bot import Bot
import codecs

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
    - Use record_play()
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

        record_play(bot): Record a play for the bot in the current turn.

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
            self.end_game(game_board)



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

        # Once the round has been started, record each bot's prompt into the
        # HistoryManager. Prompts are stored as a list of dictionaries with
        # `bot_id` and `prompt` fields. This replaces the old prompt_history
        # mechanism.
        if self.current_round is not None:
            self.current_round["prompts"] = []  # reset
            for b in game.bots:
                prompt_text = b.current_prompt or ""
                self.current_round["prompts"].append(
                    {"bot_id": b.id, "prompt": prompt_text}
                )

                # For UI navigation, reset each bot's prompt history cursor
                b.prompt_history_index = None

        # Reset current turn, this is a new round
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
            "plays": [],
            "cmd": "",
            "post_state": {},
        }

        # Snapshot pre-turn state of all bots
        self.current_turn["pre_state"] = self._get_bots_state(game)

        # Add this turn to the current round's turn list
        self.current_round["turns"].append(self.current_turn)


    def record_play(self, bot: Bot):
        """
        Record a play for the bot in the current turn.
        This includes the bot's LLM response and the command it executed.
        """


        if not self.current_turn:
            # raise ValueError(
            #    "Cannot record a play without an active turn. Call start_turn first."
            # )
            print("Cannot record a play without an active turn. Call start_turn first.")

        else:
            # Create a play entry
            play = {
                "bot_id": bot.id,
                "llm_response": bot.last_llm_response,
                "cmd": bot.last_cmd,
            }

            # Append to the current turn's plays
            self.current_turn.setdefault("plays", []).append(play)



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




    def get_chat_history(self, bot_id: int | None = None, shared: bool = True) -> list[dict[str, str]]:
        """Reconstruct the chat history for the current game.
        """
        history: list[dict[str, str, str]] = []
        # If there is no active game, return empty history.
        if not self.current_game:
            return history

        # Iterate over all completed rounds and their turns.
        rounds = self.current_game.get("rounds", [])
        for rnd in rounds:
            for turn in rnd.get("turns", []):
                for play in turn.get("plays", []):
                    history.append(
                        {"bot_id": play["bot_id"], "llm_response": play["llm_response"], "cmd": play["cmd"]})



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
                bot_info["current_prompt"] = bot.get_current_prompt()
                bot_info["last_llm_response"] = bot.last_llm_response

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
            filepath, "w", encoding="utf-8"
        ) as f:  # JSON spec requires UTF-8 support by decoders.
            json.dump(self.games, f, indent=4, ensure_ascii=False)


    # Get the full session history as a human - readable string.
    def to_text(self, include_timestamps=False, include_messages=False):
        """
        Get the full history in a human-readable indented text format (key: value style).
        Returns a multi-line string.
        """
        lines = []
        game_num = 1

        for game in self.games:

            # Game Number
            lines.append(f"Game {game_num}:")
            game_num += 1

            # Game-level details
            if include_timestamps:
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
                    lines.append("    Bots: " + ", ".join(bot_states))

            # All of the game's rounds
            for round_entry in game.get("rounds", []):
                rnd = round_entry.get("round")
                lines.append(f"    Round {rnd}:")


                if include_timestamps:
                    if "start_time" in round_entry:
                        lines.append(f"        Start: {round_entry['start_time']}")

                # All of the turns in this round:
                for turn in round_entry.get("turns", []):
                    tnum = turn.get("turn")

                    # Turn header line
                    lines.append(f"        Turn {tnum}:")

                    # For each bot, for each variable, show its values at before and after the turn.

                    # TODO check this
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
                                lines.append(
                                    f"            {bot_id} HP: {pre_hp}")

                            else:
                                change = (
                                    post_hp - pre_hp
                                    if isinstance(pre_hp, (int, float))
                                    and isinstance(post_hp, (int, float))
                                    else None
                                )

                                if change is None:
                                    # If not numeric or can't compute change, just show arrow
                                    lines.append(
                                        f"            {bot_id} HP: {pre_hp} -> {post_hp}"
                                    )
                                else:
                                    # Show change with sign
                                    sign = "+" if change > 0 else ""
                                    lines.append(
                                        f"            {bot_id} HP: {pre_hp} -> {post_hp} ({sign}{change})"
                                    )

                        # we can show how other attributes changed as well.

                    # If a bot died during this turn (alive became false), mark it
                    for bot_id, pre_info in pre.items():
                        pre_alive = pre_info.get("health", 0) > 0
                        post_alive = post.get(bot_id, {}).get("health", 0) > 0

                        if pre_alive and post_alive is False:  # was alive, now not
                            lines.append(f"            [{bot_id} died]")

                    # messages
                    if include_messages:
                        for play in turn.get("plays", []):
                            bot_id = play.get("bot_id")
                            llm_response = play.get("llm_response")
                            cmd = play.get("cmd")

                            if bot_id is not None:
                                lines.append(
                                    f'            [{bot_id}] LLM Response: "{llm_response}"')
                                lines.append(f'            [{bot_id}] Command: {cmd}')

                # Round end and winner
                if include_timestamps:
                    if "end_time" in round_entry:
                        lines.append(f"        End: {round_entry['end_time']}")

            # Game winner
            if "winner" in game:
                win = game["winner"]

                lines.append(f"    Winner: {win if win else '(none)'}")

            # Blank line between sessions if multiple
            lines.append("")

        return "\n".join(lines)



    # Get a compact, UI - friendly summary of the session history.
    def to_compact_text(self, include_timestamps=False, include_messages=True) -> str:
        """Produce a readable, Markup-decotrated, compact summary of the history for the UI left pane.

        Structure:
        - Game header and start time
        - For each round: header, prompts per bot
        - For each turn: commands per bot and post-turn state snapshot
        """

        if not self.games:
            return "No history yet. Play a round to see events here."

        out: list[str] = []

        for g_idx, game in enumerate(self.games, 1):

            out.append(
                f"[size=20sp][color=#FF0000]Game {g_idx}[/color][/size]")

            if include_timestamps:
                if game.get("start_time"):
                    out.append(f"  Start: {game['start_time']}")

            for round_entry in game.get("rounds", []):
                rnum = round_entry.get("round")
                out.append(f"  [b]Round {rnum}[/b]")

                prompts = round_entry.get("prompts", [])
                if prompts:
                    out.append("    Prompts:")
                    for p in prompts:
                        prompt_txt = escape_markup(str(p.get('prompt', '')))
                        out.append(
                            f"      Bot {p.get('bot_id')}: {prompt_txt}")

                for turn in round_entry.get("turns", []):
                    tnum = turn.get("turn")
                    out.append(f"    Turn {tnum}")

                    if include_messages:
                        # Aggregate per-bot messages for this turn
                        for play in turn.get("plays", []):
                            bot_id = play.get("bot_id")
                            llm_response = escape_markup(str(play.get("llm_response", "")))
                            cmd = escape_markup(str(play.get("cmd", "")))

                            if bot_id is not None:
                                out.append(
                                    f'      Bot {bot_id}: llm "{llm_response}" -> cmd="{cmd}"')



                    # Post-turn state
                    post = turn.get("post_state", {})
                    if post:
                        out.append("      State:")
                        for b_id, info in post.items():
                            x = info.get("x")
                            y = info.get("y")
                            rot = info.get("rot")
                            hp = info.get("health")
                            shield = info.get("shield")
                            out.append(
                                f"        Bot {b_id}: x={x:.3f} y={y:.3f} rot={rot:.1f}d health={hp} shield={'ON' if shield else 'OFF'}"
                                if isinstance(x, (int, float)) and isinstance(y, (int, float)) and isinstance(rot, (int, float))
                                else f"        Bot {b_id}: health={hp} shield={'ON' if shield else 'OFF'}"
                            )

            if game.get("winner") is not None:
                out.append(f"  Winner: {game['winner']}")
            out.append("")

        return "\n".join(out).rstrip()






    # Get a compact, per - bot summary of the session history.
    def to_compact_text_for_bot(self, bot_id: int) -> str:

        """Produce a compact, per-bot history summary for the UI left pane.

        Format example:
        Game 1
          Round 1.
            Prompt: <bot's prompt at round start>
            state: <initial state summary>
            Turn 1:
                llm res -> cmd cmd
                cmd: <parsed command>
                state: <post-action state summary>

        Notes:
        - Only includes entries for the specified bot.
        - Does not include timestamps or the bot id in lines (it's implied).
        """
        if not self.games:
            return "No history yet."

        def fmt_state(info: dict | None) -> str:
            if not isinstance(info, dict):
                return ""
            x = info.get("x")
            y = info.get("y")
            rot = info.get("rot")
            hp = info.get("health")
            shield = info.get("shield")
            if isinstance(x, (int, float)) and isinstance(y, (int, float)) and isinstance(rot, (int, float)):
                return f"x={x:.3f} y={y:.3f} rot={rot:.1f}d health={hp} shield={'ON' if shield else 'OFF'}"
            return f"health={hp} shield={'ON' if shield else 'OFF'}"

        def set_newlines(text: str, newlines=1) -> str:
            """Ensure text ends with a specific number of newlines."""
            return text.rstrip("\n") + "\n" * (newlines - 1)

        lines: list[str] = []

        for gi, game in enumerate(self.games, start=1):
            lines.append(set_newlines(
                f"[b][color=#2a2a90][size=35sp]Game {gi}[/size][/color][/b]", 2))

            for round_entry in game.get("rounds", []):
                rnum = round_entry.get("round")
                lines.append(set_newlines(
                    f"[size=26sp][b]Round {rnum}.[/b][/size]", 1))

                # Prompt at round start (for this bot only)
                prompt_text = ""
                for p in round_entry.get("prompts", []):
                    if int(p.get("bot_id", -1)) == int(bot_id):
                        prompt_text = p.get("prompt", "")
                        break

                if prompt_text:
                    prompt_text = escape_markup(str(prompt_text))
                    lines.append(set_newlines(
                        f"\n[size=18sp][b]Prompt:[/b]\n", 1))

                    for lin in prompt_text.split("\n"):
                        lines.append(f"[i]{lin.strip()}[/i]\n")
                    lines.append("[b][/prompt][/b]")


                # Initial state at round start (this bot only)
                init_state = None
                try:
                    init_state = round_entry.get(
                        "initial_state", {}).get(bot_id)

                except Exception:
                    init_state = None

                if init_state is not None:
                    lines.append(set_newlines(
                        f"[b]State:[/b]  {fmt_state(init_state)}", 2))
                    lines.append("......................")

                # Turns
                for turn in round_entry.get("turns", []):
                    tnum = turn.get("turn")
                    lines.append(set_newlines(f"[b][size=28sp]Turn {tnum}:[/size][/b]", 1))

                    for play in turn.get("plays", []) or []:
                        if int(play.get("bot_id", -1)) == int(bot_id):
                            llm_response = escape_markup(str(play.get("llm_response", "")).strip())
                            cmd = escape_markup(str(play.get("cmd", "")).strip())
                            lines.append(
                                f"[b][color=#208020][llm response][/color][/b]\n"
                            )

                            for lin in llm_response.split("\n"):
                                lines.append(f"[i][color=#208020]{lin.strip()}[/color][/i]")

                            lines.append("[/llm response]")
                            lines.append(f"[b][color=#af0000]cmd: {cmd}[/color][/b]")

                            break

                    # Post-action state (if recorded for this bot); otherwise fall back to turn post_state
                    post_action = (turn.get("post_action_states", {}) or {}).get(int(bot_id))
                    if post_action is None:
                        post_action = (turn.get("post_state", {}) or {}).get(bot_id)

                    if post_action is not None:
                        lines.append(set_newlines(f"[b]state: {fmt_state(post_action)}[/b]", 1))

                    lines.append("")

            # Blank line between games
            lines.append("")

        return "\n".join(lines).rstrip()
