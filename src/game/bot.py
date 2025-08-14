import json
import math
import random
import os
from math import cos, sin

from kivy.clock import Clock
from kivy.core.text import Label
from kivy.graphics import (
    Color,
    Ellipse,
    Line,
    PopMatrix,
    PushMatrix,
    Rectangle,
    Rotate,
    Scale,
    Translate,
)

# UrlRequest is now used within the OllamaConnector; it is no longer imported here
from kivy.properties import NumericProperty, ObjectProperty  # type: ignore[import]
from kivy.uix.widget import Widget

from configs.app_config import config
from game.bullet import Bullet
from util.normalized_canvas import NormalizedCanvas
import sys


class Bot(Widget):
    """
     This class models a game bot.

    Args:
        Widget (_type_): Kivy's base Widget class

    """

    id = NumericProperty(0)
    x = NumericProperty(0)
    y = NumericProperty(0)
    rot = NumericProperty(0)  # in degrees
    shield = ObjectProperty(None)
    health = NumericProperty(0)
    board_widget = ObjectProperty(None)

    # Note: prompt_history and prompt_history_index have been superseded by
    # the HistoryManager. We keep them here only for backward compatibility
    # with the HomeScreen UI, but they are unused. All prompts are now
    # recorded via the HistoryManager and accessed through `current_prompt`.
    prompt_history = None
    prompt_history_index = None
    ready_for_next_round = None
    ready_for_next_turn = None
    augmenting_prompt = None
    independent_models = None

    llm_endpoint = None
    llm_port = None
    shield_range_deg = None
    step = None
    diameter = None
    color = None

    last_llm_response = None

    def __init__(self, bot_id, board_widget, **kwargs):
        """Constructor

        Args:
            bot_id (_type_): the bot id
            board_widget (_type_): its parent, that is the game board where the bot lives.
        """
        super().__init__(**kwargs)

        self.id = bot_id
        # Current prompt entered by the player. Maintains the text for the
        # most recently submitted prompt. Used for constructing chat
        # messages and for UI history navigation.
        self.current_prompt: str | None = None

        # Index into this bot's prompt history when navigating through past
        # prompts. The actual history is stored by the HistoryManager on
        # the game board. This index refers to the position of the prompt
        # within the filtered list of prompts for this bot id.
        self.history_prompt_index: int | None = None
        self.board_widget = board_widget
        self.ready_for_next_round = False
        self.ready_for_next_turn = False

        self.augmenting_prompt = config.get("game", "prompt_augmentation")
        self.independent_models = config.get("game", "independent_models")

        if bot_id == 1:
            self.color = (0.8, 0.88, 1, 0.85)
        elif bot_id:
            self.color = (0.8, 0.65, 0.9, 0.85)
        else:
            self.color = (0, 1, 0, 1)

        # Build the LLM endpoint from the configured URL, port and path.
        # Note: use single quotes inside the f-string to avoid conflicting with the outer quotes.
        self.llm_endpoint = f"{config.get('llm', 'url')}:{config.get('llm', 'port')}{config.get('llm', 'path')}"

        self.diameter = config.get("game", "bot_diameter")
        self.shield = config.get("game", "shield_initial_state")
        self.shield_range_deg = config.get("game", "shield_size")
        self.health = config.get("game", "initial_health")
        self.step = config.get("game", "step_length")

        # Set initial random position and rotation
        self.x = random.uniform(0, 1)
        self.y = random.uniform(0, 1)
        self.rot = random.uniform(0, 359)

        # For independent-context mode we maintain a chat history per bot.
        # In shared-context mode the GameBoard will maintain the chat
        # history instead. Each entry is a dict with `role` and `content`.
        self.chat_history: list[dict[str, str]] = []

    def render(self):
        """Draws itself. It assumes a NormalizedCanvas."""
        r = self.diameter / 2
        d = self.diameter

        PushMatrix()
        Translate(self.x, self.y)

        Rotate(math.degrees(self.rot), 0, 0, 1)  # change all rot to degrees

        Color(*self.color)  # fill
        Ellipse(pos=(-r, -r), size=(d, d))

        Color(0, 0, 0, 0.7)  # outline
        Line(ellipse=(-r, -r, d, d), width=0.002)

        # pointing direction
        Line(points=(0, 0, r, 0), width=0.002)

        # shield
        if self.shield:
            Color(0.7, 0.5, 1, 1)
            Color(0.3, 0.3, 0.6, 1)
            Line(
                ellipse=(
                    -r,
                    -r,
                    d,
                    d,
                    90 - self.shield_range_deg,
                    90 + self.shield_range_deg,
                ),
                width=0.007,
            )  # shield_range is in degrees

        PopMatrix()

        # info box
        PushMatrix()

        x = min(0.95 - 0.116, self.x + 0.01)
        y = min(0.97 - 0.101, self.y)

        sx = r
        sy = 0.005

        Translate(x, y)
        Color(0, 0, 0, 0.2)
        Line(rectangle=(sx, sy, 0.107, 0.116), width=0.001)

        Color(1, 1, 1, 0.6)
        Rectangle(pos=(sx, sy), size=(0.107, 0.116))

        t = (
            f"x: {self.x:.3f}\n"
            f"y: {self.y:.3f}\n"
            f"rot: {self.rot:1.2f}r / {math.degrees(self.rot):3.0f}d\n"
            f"shield: {'ON' if self.shield else 'OFF'}\n"
            f"health: {self.health}"
        )

        Color(0, 0, 0, 0.7)
        mylabel = Label(text=t, font_size=24, color=(0, 0, 0, 0.7))
        mylabel.refresh()
        texture = mylabel.texture
        Rectangle(pos=(0.064, 0.109), texture=texture, size=(0.081, -0.101))
        # /info box

        PopMatrix()

    def move(self):
        """The bot takes a step. Corresponds to the command 'M'"""
        self.x += self.step * cos(self.rot)
        self.y += self.step * sin(self.rot)

    def rotate(self, angle):
        """The bot rotates by a given angle. Corresponds to the commands 'C' and 'A'"""
        self.rot += angle
        self.rot = math.fmod(self.rot, 2 * math.pi)

    def append_prompt_to_history(self, new_prompt):
        # Deprecated: prompts are now recorded through the HistoryManager.
        # This method is retained for backward compatibility but does nothing.
        pass

    def rewind_prompt_history(self):
        """Selects the previous prompt for this bot from the history manager.

        This method navigates through the list of prompts stored by the
        HistoryManager for this bot. When called, it moves the cursor
        backwards if possible and updates `current_prompt` accordingly.
        """

        # Fetch prompts for this bot from the HistoryManager
        prompts = []
        if (
            self.board_widget.history_manager.current_round
            and "prompts" in self.board_widget.history_manager.current_round
        ):
            prompts = [
                p["prompt"]
                for p in self.board_widget.history_manager.current_round["prompts"]
                if p.get("bot_id") == self.id
            ]

        # Determine the new index
        if self.history_prompt_index is None:
            # Start from the end
            if prompts:
                self.history_prompt_index = len(prompts) - 1
        else:
            if self.history_prompt_index > 0:
                self.history_prompt_index -= 1

        # Update current_prompt based on the new index
        if (
            self.history_prompt_index is not None
            and 0 <= self.history_prompt_index < len(prompts)
        ):
            self.current_prompt = prompts[self.history_prompt_index]

    def forward_prompt_history(self):
        """Selects the next prompt for this bot from the history manager.

        Navigates forwards through this bot's prompt history maintained
        by the HistoryManager and updates `current_prompt`.
        """

        prompts = []
        if (
            self.board_widget.history_manager.current_round
            and "prompts" in self.board_widget.history_manager.current_round
        ):
            prompts = [
                p["prompt"]
                for p in self.board_widget.history_manager.current_round["prompts"]
                if p.get("bot_id") == self.id
            ]

        if self.history_prompt_index is None:
            # If no index set, start at first prompt if any
            if prompts:
                self.history_prompt_index = 0
        else:
            if self.history_prompt_index < len(prompts) - 1:
                self.history_prompt_index += 1

        if (
            self.history_prompt_index is not None
            and 0 <= self.history_prompt_index < len(prompts)
        ):
            self.current_prompt = prompts[self.history_prompt_index]

    def get_current_prompt_from_history(self):
        """Retrieve the currently selected prompt for this bot.

        The HistoryManager holds all prompts submitted by both bots. The
        `history_prompt_index` points into the filtered list of prompts
        belonging to this bot. If no prompt is selected, an empty
        string is returned.

        Returns:
            str: The prompt text or an empty string.
        """
        return self.current_prompt or ""

    def get_current_prompt(self):
        """Returns the current prompt. It is equivalent to get_prompt.

        Returns:
            _type_: a string with the prompt
        """
        return self.get_current_prompt_from_history()

    def get_prompt(self):
        """Returns the current prompt. It is equivalent to get_current_prompt_from_history.
        Returns:
            _type_: a string with the prompt
        """
        return self.get_current_prompt_from_history()

    def set_augmenting_prompt(self, augmenting):
        """Toggles the flag indicating if the player prompts are augmented with game info.

        Args:
            augmenting (_type_): the new flag value
        """
        self.augmenting_prompt = augmenting

    def get_augmenting_prompt(self, augmenting):
        """Toggles the flag indicating if the player prompts are augmented with game info.

        Args:
            augmenting (_type_): the new flag value
        """
        return self.augmenting_prompt

    def prepare_prompt_submission(self, new_prompt):
        """Store a new prompt and mark the bot ready for the next round.

        Args:
            new_prompt (str): the player's prompt to use.
        """
        # Store the prompt for reference in UI and LLM interaction
        self.current_prompt = new_prompt

        # Reset history navigation index so that the new prompt becomes the
        # default selected prompt when the round starts.
        self.history_prompt_index = None

        # Mark the bot as ready for a new round
        self.ready_for_next_round = True

    def submit_prompt_to_llm(self):
        """Prepare and send a chat-style request to the LLM via the board's OllamaConnector.

        This method assembles a list of chat messages following the chat API
        convention. A system message containing the appropriate header is
        included at the start of the conversation. The player's input is
        encoded as a user message along with optional game state and
        history information when prompt augmentation is enabled. Previous
        messages are retained either on a per-bot basis (independent
        context) or shared for both bots (shared context). The assembled
        messages are then sent to the `/api/chat` endpoint.
        """
        # Refresh config flags in case the user changed them via the UI
        self.augmenting_prompt = config.get("game", "prompt_augmentation")
        self.independent_models = config.get("game", "independent_models")

        # Determine which header to use based on independent/shared context
        header_key = (
            "augmentation_header_independent"
            if self.independent_models
            else "augmentation_header_dependent"
        )
        header_path = config.get("llm", header_key)
        # Fall back to shared header if dependent key not configured
        try:
            with open(header_path, "r", encoding="utf-8") as f:
                header_text = f.read()
        except FileNotFoundError:
            # Attempt to load a sensible shared header file if the configured
            # dependent path is missing. This falls back to
            # `augmentation_header_shared_1.txt` located in the same directory.
            shared_fallback = os.path.join(
                os.path.dirname(header_path), "augmentation_header_shared_1.txt"
            )
            try:
                with open(shared_fallback, "r", encoding="utf-8") as f:
                    header_text = f.read()
            except Exception:
                header_text = ""

        # Build the system message only at the beginning of a conversation. If the
        # chat history is empty (meaning this is the first call), prepend a
        # system message containing the instructions. Otherwise, the system
        # message will already reside at index 0 in the chat history.
        system_message = {"role": "system", "content": header_text}

        # Determine which chat history to use
        if self.independent_models:
            chat_history = self.chat_history
        else:
            chat_history = self.board_widget.chat_history_shared

        messages: list[dict[str, str]] = []

        if not chat_history:
            # Start the conversation with the system message if no history exists
            messages.append(system_message)
        else:
            # Copy existing chat history (includes system and previous exchanges)
            messages.extend(chat_history)

        # Build the user message including optional game state and the current
        # prompt. The format of this content matches the previous
        # non-chat prompt structure for continuity.
        user_content = ""
        if self.augmenting_prompt:
            user_content += "GAME_STATE:\n"
            user_content += f"Self.x: {self.x}, Self.y: {self.y}\n"
            user_content += f"Self.rot: {math.degrees(self.rot)}\n"
            user_content += f"Self.shield: {'ON' if self.shield else 'OFF'}\n"
            user_content += f"Self.health: {self.health}\n"
            # Opponent info
            opp = self.board_widget.get_bot_by_id(3 - self.id)
            user_content += (
                f"Opponent.x: {opp.x}, Opponent.y: {opp.y}\n"
                f"Opponent.rot: {math.degrees(opp.rot)}\n"
                f"Opponent.shield: {'ON' if opp.shield else 'OFF'}\n"
                f"Opponent.health: {opp.health}\n"
            )
            user_content += "PLAYER_INPUT:\n"
            user_content += (self.current_prompt or "") + "\n"
        else:
            # Only include the player's input
            user_content += "PLAYER_INPUT:\n"
            user_content += (self.current_prompt or "") + "\n"

        # Always append the game history
        user_content += "GAME_HISTORY:\n"
        try:
            user_content += self.board_widget.history_manager.to_text()
        except Exception:
            # Fallback to empty history if conversion fails
            user_content += ""

        # Create the user message and append to the messages list
        user_message = {"role": "user", "content": user_content}
        messages.append(user_message)

        # Build the payload expected by the chat API
        data = {
            "model": config.get("llm", "model"),
            "messages": messages,
            "stream": False,
        }

        # Construct the full URL for the chat endpoint (override the configured path)
        base_url = config.get("llm", "url")
        port = config.get("llm", "port")
        # Always use the chat path regardless of `llm.path` in the config
        chat_url = f"{base_url}:{port}/api/chat"

        # Send the request via the shared OllamaConnector. It will call the
        # appropriate callback on completion.
        self.board_widget.ollama_connector.send_request(
            chat_url,
            data,
            self._on_llm_response,
            self._on_llm_failure,
            self._on_llm_error,
        )

    def _on_llm_failure(self, request, error):
        """Error handler for HTTP errors 4xx, 5xx

        Args:
            request (_type_): the request object
            error (_type_): the error obtained
        """

        self.board_widget.on_bot_llm_interaction_complete(self)

    def _on_llm_error(self, request, error):
        """Error handler for errors outside the web protocol (no connection, etc)

        Args:
            request (_type_): the request object
            error (_type_): the error obtained
        """

        self.board_widget.on_bot_llm_interaction_complete(self)

    def _on_llm_response(self, req, result):
        """Event handler of a successul interaction with the LLM

        Args:
            req (_type_): the request object
            result (_type_): the interaction result

        """

        # Extract the assistant's content from the result. Different chat
        # backends may return slightly different JSON structures, so we
        # inspect several common fields. Ultimately we fall back to an
        # empty string if none of the expected keys are present.
        assistant_content = ""
        try:
            if isinstance(result, dict):
                if isinstance(result.get("response"), str):
                    assistant_content = result["response"]
                elif isinstance(result.get("message"), dict) and isinstance(
                    result["message"].get("content"), str
                ):
                    assistant_content = result["message"]["content"]
                elif (
                    isinstance(result.get("choices"), list)
                    and len(result["choices"]) > 0
                    and isinstance(result["choices"][0], dict)
                ):
                    choice = result["choices"][0]
                    if isinstance(choice.get("message"), dict) and isinstance(
                        choice["message"].get("content"), str
                    ):
                        assistant_content = choice["message"]["content"]
                # Sometimes the API returns the content directly in `content` key
                elif isinstance(result.get("content"), str):
                    assistant_content = result["content"]
        except Exception:
            assistant_content = ""

        # Clean up whitespace
        assistant_content = (
            assistant_content.strip() if isinstance(assistant_content, str) else ""
        )

        # Store the last LLM response for logging
        self.last_llm_response = assistant_content

        cmd = assistant_content

        command = None

        # ********* Processing the response *********
        command_ok = True
        try:
            if isinstance(cmd, str):
                command = cmd
            elif isinstance(cmd, list) and len(cmd) > 0:
                command = cmd[0]
            else:
                command_ok = False

            if command_ok:
                match command[0]:
                    case "M":
                        self.board_widget.add_llm_response_to_history(self.id, "M")
                        self.move()

                    case "C":
                        angle = float(command[1:])
                        self.board_widget.add_llm_response_to_history(
                            self.id, f"C{angle}"
                        )
                        self.rotate(angle)

                    case "A":
                        angle = float(command[1:])
                        self.board_widget.add_llm_response_to_history(
                            self.id, f"A{angle}"
                        )
                        self.rotate(-angle)

                    case "B":
                        self.board_widget.shoot(self.id)
                        self.board_widget.add_llm_response_to_history(self.id, "B")

                    case "S":
                        if len(command) == 1:
                            self.board_widget.add_llm_response_to_history(self.id, "S")
                            self.toggle_shield()

                        else:
                            if command[1] == "1":
                                self.board_widget.add_llm_response_to_history(
                                    self.id, "S1"
                                )
                                self.shield = True

                            elif command[1] == "0":
                                self.board_widget.add_llm_response_to_history(
                                    self.id, "S0"
                                )
                                self.shield = False
                            else:
                                command_ok = False
                    case _:
                        command_ok = False

        except Exception as e:
            command_ok = False
            print(f"exception: {e}")

        if not command_ok:
            self.log(f"\n\n[color=#FF0000][b]Invalid Command.[/b][/color]\n\n")
            self.board_widget.add_llm_response_to_history(self.id, "ERR")

        # ********* Update the chat history with the user and assistant messages *********
        # Determine which chat history to update based on independent/shared context
        history_list = (
            self.chat_history
            if self.independent_models
            else self.board_widget.chat_history_shared
        )

        # If the history is empty, add the system message first (same logic as in submit_prompt_to_llm)
        if not history_list:
            header_key = (
                "augmentation_header_independent"
                if self.independent_models
                else "augmentation_header_dependent"
            )
            header_path = config.get("llm", header_key)
            header_text = ""
            try:
                with open(header_path, "r", encoding="utf-8") as f:
                    header_text = f.read()
            except FileNotFoundError:
                # Fall back to a shared header file in the same directory
                shared_fallback = os.path.join(
                    os.path.dirname(header_path), "augmentation_header_shared_1.txt"
                )
                try:
                    with open(shared_fallback, "r", encoding="utf-8") as f:
                        header_text = f.read()
                except Exception:
                    header_text = ""
            except Exception:
                header_text = ""

            history_list.append({"role": "system", "content": header_text})

        # Build the user message content just like in submit_prompt_to_llm
        user_content = ""
        if self.augmenting_prompt:
            user_content += "GAME_STATE:\n"
            user_content += f"Self.x: {self.x}, Self.y: {self.y}\n"
            user_content += f"Self.rot: {math.degrees(self.rot)}\n"
            user_content += f"Self.shield: {'ON' if self.shield else 'OFF'}\n"
            user_content += f"Self.health: {self.health}\n"
            opp = self.board_widget.get_bot_by_id(3 - self.id)
            user_content += (
                f"Opponent.x: {opp.x}, Opponent.y: {opp.y}\n"
                f"Opponent.rot: {math.degrees(opp.rot)}\n"
                f"Opponent.shield: {'ON' if opp.shield else 'OFF'}\n"
                f"Opponent.health: {opp.health}\n"
            )
            user_content += "PLAYER_INPUT:\n"
            user_content += (self.current_prompt or "") + "\n"
        else:
            user_content += "PLAYER_INPUT:\n"
            user_content += (self.current_prompt or "") + "\n"
        user_content += "GAME_HISTORY:\n"
        try:
            user_content += self.board_widget.history_manager.to_text()
        except Exception:
            user_content += ""

        # Append the user message and the assistant's response to the history
        history_list.append({"role": "user", "content": user_content})
        history_list.append({"role": "assistant", "content": assistant_content})

        # ********* Updating the bot's state and notifying the board widget *********
        self.ready_for_next_turn = True
        self.board_widget.on_bot_llm_interaction_complete(self)

    def damage(self):
        """The bot's been hit"""
        self.health -= config.get("game", "bullet_damage")
        self.health = max(self.health, 0)

    def toggle_shield(self):
        """Toggles the shield state."""
        self.shield = not self.shield

    def create_bullet(self):
        """Tries to shoot a bullet. It will only succeed if the shield is down.

        Returns:
            _type_: the bullet shot or None
        """
        if not self.shield:
            return Bullet(self.id, self.x, self.y, self.rot)

        else:
            return None
