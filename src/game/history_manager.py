import json  # noqa: E402
from datetime import datetime
from configs.app_config import config

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
    def __init__(self):
        """Initialize a new HistoryManager with no active game."""
        self.games = []  # List of games played in this session (BotLLM run)
        self.current_game = None  # Dictionary for the current game's history
        self.current_round = None  # Dictionary for the current round's history
        self.current_turn = None  # Dictionary for the current turn's history

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
        bots_state = self._get_bots_state(game_board)
        self.current_game["initial_state"] = bots_state

        # Append this session to sessions list
        self.games.append(self.current_game)

        # Reset current round/turn since new game
        # TODO create a new round at game start
        # Can use a parameter to indicate it is the first one
        # or it could be a different method, start_first_round
        # or it could be part of the game_board.start_new_game
        # self.start_round(self.current_game, first_round=True)
        self.current_round = None
        self.current_turn = None

    def end_game(self, game, force=False):
        """
        End the current game. This can be called at any time (e.g., normal game end or aborted mid-round).
        It finalizes any ongoing round/turn and records the end time and final outcome.
        The parameter `force` is used internally to finalize a game without double-calling end_game recursively.
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

    def start_round(self, game, first_round=False):
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

        # TODO review this logic
        # If not the first round, ensure no round is currently active
        # if not first_round:
        #    # If we were already in a round, then raise an error
        #    if self.current_round and "end_time" not in self.current_round:
        #             "Cannot start a round while in one. Call end_round first."
        #         )
        #        raise ValueError(

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

        # Reset current turn
        self.current_turn = None

    def end_round(self, game):
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
                raise ValueError("Cannot end a round mid turn. Call end_turn first")

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
            # ``messages`` will be lazily created when the first message is recorded.
            # It will store chat-style interactions between the bot and the LLM for this turn.
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
            raise ValueError("Cannot end a non-existent turn. Call start_turn first.")

        # Record the turn's end time
        self.current_turn["end_time"] = self._now_iso()

        # Snapshot post-turn state of all bots
        self.current_turn["post_state"] = self._get_bots_state(game)

        # Clear current_turn (it remains in the turns list of the round)
        self.current_turn = None

    # -------------------------------------------------------------------------
    # Chat history management
    #
    # The following helper methods allow the game code to record and retrieve
    # chat messages without duplicating state across classes. Each bot calls
    # ``record_message`` to persist user and assistant messages into the
    # current turn. ``get_chat_history`` reconstructs the conversation up to
    # the present, optionally filtering by bot when independent contexts are
    # desired. This centralises all chat data within the HistoryManager.

    def record_message(self, bot_id: int, role: str, content: str) -> None:
        """Record a chat message for the current turn.

        Parameters
        ----------
        bot_id: int
            Identifier of the bot that originated the message. For assistant
            messages this should still be the bot that requested the LLM
            response.
        role: str
            The role of the message, typically ``"user"`` or ``"assistant"``.
        content: str
            The textual content of the message.

        Notes
        -----
        If no turn is currently active, this method does nothing. The
        ``messages`` list is created lazily on first use. Messages are
        appended in the order they are recorded.
        """
        # Ensure we only record messages when a turn is active.
        if not self.current_turn:
            return

        # Lazily create the messages list on the current turn.
        msgs = self.current_turn.setdefault("messages", [])
        msgs.append({"bot_id": bot_id, "role": role, "content": content})

    def get_chat_history(self, bot_id: int | None = None, shared: bool = True) -> list[dict[str, str]]:
        """Reconstruct the chat history for the current game.

        Parameters
        ----------
        bot_id: int | None, optional
            When ``shared`` is False, this specifies the bot whose messages
            should be returned. When ``shared`` is True this argument is
            ignored.
        shared: bool
            If True, messages from both bots are returned in chronological
            order. If False, only messages whose ``bot_id`` matches ``bot_id``
            are included. Defaults to True.

        Returns
        -------
        list of dict
            A list of message dictionaries with keys ``role`` and ``content``.

        Notes
        -----
        The history traverses all rounds and turns of the current game. If
        there is no current game or no rounds have been played, an empty list
        is returned.
        """
        history: list[dict[str, str]] = []
        # If there is no active game, return empty history.
        if not self.current_game:
            return history

        # Iterate over all completed rounds and their turns.
        rounds = self.current_game.get("rounds", [])
        for rnd in rounds:
            for turn in rnd.get("turns", []):
                for msg in turn.get("messages", []):
                    if shared or bot_id is None:
                        history.append({"role": msg["role"], "content": msg["content"]})
                    else:
                        # Only include messages from the specified bot.
                        if msg.get("bot_id") == bot_id:
                            history.append({"role": msg["role"], "content": msg["content"]})

        # Also include any messages recorded in the current turn (if it exists).
        if self.current_turn and "messages" in self.current_turn:
            for msg in self.current_turn["messages"]:
                if shared or bot_id is None:
                    history.append({"role": msg["role"], "content": msg["content"]})
                else:
                    if msg.get("bot_id") == bot_id:
                        history.append({"role": msg["role"], "content": msg["content"]})

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

        else:
            # Fallback: check common attribute names for two players scenario
            if hasattr(game, "bot1"):
                bots.append(game.bot1)

            if hasattr(game, "bot2"):
                bots.append(game.bot2)

        # Iterate over the collected bot objects and record their state
        for bot in bots:
            if not bot:
                continue

            # TODO check if bot has an id attribute, otherwise use a default or raise an error
            bot_id = bot.id  # TODO check this

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

        with open(
            filepath, "w", encoding="utf-8"
        ) as f:  # JSON spec requires UTF-8 support by decoders.
            json.dump(self.games, f, indent=4, ensure_ascii=False)

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

            # Game Number
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
                    lines.append("    Bots: " + ", ".join(bot_states))

            # All of the game's rounds
            for round_entry in game.get("rounds", []):
                rnd = round_entry.get("round")
                lines.append(f"    Round {rnd}:")

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
                                lines.append(f"            {bot_id} HP: {pre_hp}")

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

    # ------------------------------------------------------------------
    # Compact, reader-friendly summary for the History screen (left pane)
    def _extract_player_input_summary(self, content: str) -> str:
        """Extract a single-line summary of the player's input from a user message content.

        Looks for the section after "PLAYER_INPUT:" and returns the first non-empty
        line. Falls back to trimming the whole content if the marker is absent.
        """
        if not isinstance(content, str):
            return ""
        marker = "PLAYER_INPUT:"
        try:
            idx = content.find(marker)
            snippet = content[idx + len(marker) :] if idx >= 0 else content
            for line in snippet.splitlines():
                s = line.strip()
                if s:
                    return s
        except (AttributeError, TypeError, ValueError):
            pass
        return content.strip().splitlines()[0] if content else ""

    def to_compact_text(self) -> str:
        """Produce a readable, compact summary of the history for the UI left pane.

        Structure:
        - Game header and start time
        - For each round: header, prompts per bot
        - For each turn: commands per bot and post-turn state snapshot
        """
        if not self.games:
            return "No history yet. Play a round to see events here."

        out: list[str] = []
        for g_idx, game in enumerate(self.games, 1):
            out.append(f"Game {g_idx}")
            if game.get("start_time"):
                out.append(f"  Start: {game['start_time']}")

            for round_entry in game.get("rounds", []):
                rnum = round_entry.get("round")
                out.append(f"  Round {rnum}")

                prompts = round_entry.get("prompts", [])
                if prompts:
                    out.append("    Prompts:")
                    for p in prompts:
                        out.append(f"      Bot {p.get('bot_id')}: {p.get('prompt','')}")

                for turn in round_entry.get("turns", []):
                    tnum = turn.get("turn")
                    out.append(f"    Turn {tnum}")

                    # Aggregate per-bot messages for this turn
                    per_bot: dict[int, dict[str, str]] = {}
                    for msg in turn.get("messages", []):
                        b = msg.get("bot_id")
                        if b is None:
                            continue
                        entry = per_bot.setdefault(int(b), {})
                        role = msg.get("role")
                        content = msg.get("content", "")
                        if role == "user":
                            entry["user"] = self._extract_player_input_summary(content)
                        elif role == "assistant":
                            entry["assistant"] = (content or "").strip()

                    if per_bot:
                        out.append("      Responses:")
                        for b_id in sorted(per_bot.keys()):
                            e = per_bot[b_id]
                            u = e.get("user", "")
                            a = e.get("assistant", "")
                            out.append(f"        Bot {b_id}: prompt='{u}' -> cmd='{a}'")

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
