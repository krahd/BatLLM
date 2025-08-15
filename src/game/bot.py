import math
import json
import os
import random
from math import cos, sin
from typing import Any

from kivy.core.text import Label
from kivy.graphics import (
    Color,
    Ellipse,
    Line,
    PopMatrix,
    PushMatrix,
    Rectangle,
    Rotate,
    Translate,
)

# type: ignore[import]
from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.widget import Widget

from configs.app_config import config
from game.bullet import Bullet


class Bot(Widget):
    """
    Represents a game bot. Responsible for rendering, handling actions,
    building/sending LLM requests, and parsing responses.
    """

    id = NumericProperty(0)
    x = NumericProperty(0.0)
    y = NumericProperty(0.0)
    rot = NumericProperty(0.0)  # degrees
    shield = ObjectProperty(None)
    health = NumericProperty(0)
    board_widget = ObjectProperty(None)

    # Runtime state
    current_prompt: str | None = None
    prompt_history_index: int | None = None
    ready_for_next_round: bool | None = None
    ready_for_next_turn: bool | None = None
    augmenting_prompt: bool | None = None
    independent_contexts: bool | None = None

    # Config-derived values
    shield_range_deg: float | None = None
    step: float | None = None
    diameter: float | None = None
    color: tuple[float, float, float, float] | None = None

    last_llm_response: str | None = None

    def __init__(self, bot_id: int, board_widget, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.id = bot_id
        self.board_widget = board_widget
        self.ready_for_next_round = False
        self.ready_for_next_turn = False
        self.augmenting_prompt = bool(
            config.get("game", "prompt_augmentation"))
        self.independent_contexts = bool(
            config.get("game", "independent_contexts"))

        if bot_id == 1:
            self.color = (0.8, 0.88, 1, 0.85)
        elif bot_id:
            self.color = (0.8, 0.65, 0.9, 0.85)
        else:
            self.color = (0, 1, 0, 1)

        self.diameter = float(config.get("game", "bot_diameter"))
        self.shield = bool(config.get("game", "shield_initial_state"))
        self.shield_range_deg = float(config.get("game", "shield_size"))
        self.health = int(config.get("game", "initial_health"))
        self.step = float(config.get("game", "step_length"))

        # Random initial pose
        self.x = random.uniform(0, 1)
        self.y = random.uniform(0, 1)
        self.rot = random.uniform(0, 359)  # degrees

    # ------------------------- Rendering -------------------------
    def render(self):
        """Draw this bot."""
        r = (self.diameter or 0.1) / 2
        d = self.diameter or 0.1

        PushMatrix()
        Translate(self.x, self.y)
        Rotate(self.rot, 0, 0, 1)  # rot stored in degrees

        Color(*(self.color or (1, 1, 1, 1)))
        Ellipse(pos=(-r, -r), size=(d, d))

        Color(0, 0, 0, 0.7)
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
                    90 - (self.shield_range_deg or 0),
                    90 + (self.shield_range_deg or 0),
                ),
                width=0.007,
            )

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
            f"rot: {self.rot:3.0f}d\n"
            f"shield: {'ON' if self.shield else 'OFF'}\n"
            f"health: {self.health}"
        )
        Color(0, 0, 0, 0.7)
        mylabel = Label(text=t, font_size=24, color=(0, 0, 0, 0.7))
        mylabel.refresh()
        texture = mylabel.texture
        Rectangle(pos=(0.064, 0.109), texture=texture, size=(0.081, -0.101))
        PopMatrix()

    # ------------------------- Actions -------------------------
    def move(self):
        """
        Updates the bot's position based on its current rotation and step size.

        The method calculates the new x and y coordinates by moving the bot forward in the direction
        specified by its rotation angle (`self.rot`). The movement distance is determined by `self.step`,
        defaulting to 0.02 if `self.step` is not set.

        Returns:
            None
        """
        rad = math.radians(self.rot)
        self.x += (self.step or 0.02) * cos(rad)
        self.y += (self.step or 0.02) * sin(rad)

    def rotate(self, angle: float):
        """
        Rotates the object by a specified angle.

        Args:
            angle (float): The angle in degrees to rotate the object. Positive values rotate clockwise, negative values rotate counterclockwise.

        The rotation is normalized to stay within the range [0, 360) degrees.
        """
        self.rot = (self.rot + angle) % 360

    def damage(self):
        """
        Reduces the bot's health by the bullet damage value specified in the configuration.
        Ensures that health does not drop below zero.
        """
        self.health -= int(config.get("game", "bullet_damage"))
        self.health = max(self.health, 0)

    def toggle_shield(self):
        """
        Toggles the state of the shield.

        If the shield is currently active, it will be deactivated, and vice versa.
        """
        self.shield = not self.shield

    def create_bullet(self):
        """
        Creates and returns a Bullet object if the bot's shield is not active.

        Returns:
            Bullet: A new Bullet instance initialized with the bot's id, position (x, y), and rotation (rot) if the shield is inactive.
            None: If the shield is active, no bullet is created and None is returned.
        """
        if not self.shield:
            return Bullet(self.id, self.x, self.y, self.rot)
        return None

    # Bullet helper compatibility
    def rot_rad(self):
        """
        Converts the current rotation angle from degrees to radians.

        Returns:
            float: The rotation angle in radians.
        """
        return math.radians(self.rot)

    @property
    def shield_range(self):
        """
        Returns the shield range as a float value.

        If the attribute 'shield_range_deg' is set, its value is converted to a float and returned.
        If 'shield_range_deg' is None or evaluates to False, 0.0 is returned.

        Returns:
            float: The shield range in degrees.
        """
        return float(self.shield_range_deg or 0)

    # ------------------------- Prompt history (UI helpers) -------------------------
    def rewind_prompt_history(self):
        """
        Rewinds the bot's prompt history to the previous prompt, if available.

        This method retrieves the list of prompts associated with the current round for this bot,
        and updates the prompt history index to point to the previous prompt. If the index is not set,
        it initializes it to the most recent prompt. If already set and not at the beginning, it decrements
        the index. Finally, it updates the current prompt to reflect the new index.

        Attributes used:
            self.board_widget.history_manager: The history manager containing round and prompt data.
            self.id: The bot's unique identifier.
            self.prompt_history_index: The current index in the prompt history.
            self.current_prompt: The prompt currently selected after rewinding.

        Side Effects:
            Modifies self.prompt_history_index and self.current_prompt.
        """

        prompts = []

        hm = self.board_widget.history_manager
        if hm.current_round and "prompts" in hm.current_round:
            prompts = [
                p["prompt"]
                for p in hm.current_round["prompts"]
                if p.get("bot_id") == self.id
            ]

        if self.prompt_history_index is None:
            if prompts:
                self.prompt_history_index = len(prompts) - 1

        else:
            if self.prompt_history_index > 0:
                self.prompt_history_index -= 1

        if (
            self.prompt_history_index is not None
            and 0 <= self.prompt_history_index < len(prompts)
        ):
            self.current_prompt = prompts[self.prompt_history_index]

    def forward_prompt_history(self):
        """
        Advances the prompt history index to the next prompt for the current bot, if available.

        This method retrieves the list of prompts associated with the current round and filters them
        to include only those belonging to this bot (matching `self.id`). If the prompt history index
        (`self.prompt_history_index`) is not set, it initializes it to the first prompt if any exist.
        Otherwise, it increments the index if there are more prompts ahead. Finally, it updates
        `self.current_prompt` to the prompt at the current index, if valid.

        Side Effects:
            - Updates `self.prompt_history_index` and `self.current_prompt` attributes.
        """
        prompts = []

        hm = self.board_widget.history_manager

        if hm.current_round and "prompts" in hm.current_round:
            prompts = [
                p["prompt"]
                for p in hm.current_round["prompts"]
                if p.get("bot_id") == self.id
            ]

        if self.prompt_history_index is None:
            if prompts:
                self.prompt_history_index = 0
        else:
            if self.prompt_history_index < len(prompts) - 1:
                self.prompt_history_index += 1

        if (
            self.prompt_history_index is not None
            and 0 <= self.prompt_history_index < len(prompts)
        ):
            self.current_prompt = prompts[self.prompt_history_index]

    def get_current_prompt_from_history(self):
        return self.current_prompt or ""

    def get_current_prompt(self):
        """
        Retrieves the current prompt for the bot.

        Returns:
            str: The current prompt obtained from the bot's history.
        """
        return self.get_current_prompt_from_history()

    def get_prompt(self):
        """
        Retrieves the current prompt from the conversation history.

        Returns:
            str: The current prompt extracted from the history.
        """
        return self.get_current_prompt_from_history()

    def set_augmenting_prompt(self, augmenting: bool):
        """
        Sets the augmenting prompt flag.

        Args:
            augmenting (bool): If True, enables the augmenting prompt; if False, disables it.
        """
        self.augmenting_prompt = augmenting

    def get_augmenting_prompt(self):
        """
        Returns True if an augmenting prompt is set, otherwise False.

        Returns:
            bool: True if self.augmenting_prompt is truthy, False otherwise.
        """
        return bool(self.augmenting_prompt)

    def prepare_prompt_submission(self, new_prompt: str):
        """
        Prepares the bot for submitting a new prompt.

        This method sets the current prompt to the provided `new_prompt`, resets the prompt history index,
        and marks the bot as ready for the next round.

        Args:
            new_prompt (str): The new prompt to be submitted.
        """
        self.current_prompt = new_prompt
        self.prompt_history_index = None
        self.ready_for_next_round = True

    # ------------------------- LLM communication -------------------------

    def submit_prompt_to_llm(self):
        """
        Build and send a single /api/chat request to the LLM.

        - Uses PromptBuilder to construct the full payload (shared vs independent,
        augmented vs non-augmented).
        - In history we only store the assistant's raw output and the parsed command elsewhere.
        - If augmented mode is on and the header file is missing/unreadable,
        PromptBuilder will raise RuntimeError and crash (by design).
        """
        # Local import to avoid module init order issues
        from game.prompt_builder import PromptBuilder

        shared_context = config.get("game", "independent_contexts") != "1"
        augmented = config.get("game", "prompt_augmentation") == "1"

        # Build the payload (may raise if augmented header file is missing)
        pb = PromptBuilder(
            history_manager=self.board_widget.history_manager,
            game_board=self.board_widget,
            self_bot=self,
            cfg=getattr(self, "app_config", None),
        )

        payload = pb.build_chat_payload(
            shared_context=shared_context, augmented=augmented)

        # Compose chat URL from app_config (works with configparser-like or dict-of-dicts)

        base_url = (config.get("llm", "url")).rstrip("/")
        port = config.get("llm", "port")
        path = config.get("llm", "path")
        chat_url = f"{base_url}:{port}{path}"

        # Debug outgoing payload
        if bool(config.get("llm", "debug_requests")):
            try:
                preview = json.dumps(payload, indent=2)
            except (TypeError, ValueError, OverflowError):
                preview = str(data)

            print(
                "---->>>----------------------------------------------------------------------"
            )
            print(
                f"(debug)[LLM][Bot {self.id}] POST {chat_url} with payload:\n{preview}"
            )
            print(
                "----<<<----------------------------------------------------------------------\n\n"
            )

        # Fire the async request through your existing connector
        return self.board_widget.ollama_connector.send_request(
            url=chat_url,
            data=payload,
            on_success=self._on_llm_response,
            # consider a verbose variant if you want to log resp body
            on_failure=self._on_llm_failure,
            on_error=self._on_llm_error,
        )

    

    def _get_mode_header_text(self) -> str:

        if not self.augmenting_prompt:
            return ""

        # Get the augmentation header text for the LLM request based on the mode
        key = (
            "augmentation_header_independent"
            if self.independent_contexts
            else "augmentation_header_shared"
        )

        path = config.get("llm", key)

        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()

        except FileNotFoundError:
            shared_fallback = os.path.join(
                os.path.dirname(path),
                "src/assets/prompts/augmentation_header_shared_1.txt",
            )

            try:
                with open(shared_fallback, "r", encoding="utf-8") as f:
                    return f.read()
            except OSError:
                return ""



    def _on_llm_failure(self, _request, _error):
        self.board_widget.on_bot_llm_interaction_complete(self)


    def _on_llm_error(self, _request, _error):
        self.board_widget.on_bot_llm_interaction_complete(self)


    def _on_llm_response(self, _req, result):
        """Parse the LLM reply, execute it, record history, and finish the turn."""

        
        #print(json.dumps(result, indent=2))
        print (">> result length:", len(str(result)) if result else 0)
        

        # 1) Extract assistant content from common chat API shapes
        assistant_content = ""
        try:
            if isinstance(result, dict):
                if isinstance(result.get("response"), str):
                    assistant_content = result["response"]                    

                elif isinstance(result.get("message"), dict) and isinstance(result["message"].get("content"), str):
                    assistant_content = result["message"]["content"]        

                elif (
                    isinstance(result.get("choices"), list)
                    and result["choices"]
                    and isinstance(result["choices"][0], dict)
                ):
                    choice = result["choices"][0]
                    msg = choice.get("message") if isinstance(
                        choice, dict) else None

                    if isinstance(msg, dict) and isinstance(msg.get("content"), str):
                        assistant_content = msg["content"]

                elif isinstance(result.get("content"), str):
                    assistant_content = result["content"]

        except (TypeError, KeyError, ValueError):
            assistant_content = ""

        assistant_content = (
            assistant_content.strip() if isinstance(assistant_content, str) else ""
        )
        self.last_llm_response = assistant_content

        print(f"***** last_llm_response: {assistant_content}")

        # 2) Interpret command
        cmd = assistant_content
        command_ok = True
        command: str | None = None
        try:
            if isinstance(cmd, str):
                command = cmd

            elif isinstance(cmd, list) and len(cmd) > 0:
                command = cmd[0]

            else:
                command_ok = False

            if command_ok and isinstance(command, str) and command:

                match command[0]:
                    case "M":
                        self.board_widget.add_cmd_to_home_screen_cmd_history(
                            self.id, "M")
                        self.move()

                    case "C":
                        angle = float(command[1:])
                        self.board_widget.add_cmd_to_home_screen_cmd_history(
                            self.id, f"C{angle}"
                        )
                        self.rotate(angle)

                    case "A":
                        angle = float(command[1:])
                        self.board_widget.add_cmd_to_home_screen_cmd_history(
                            self.id, f"A{angle}"
                        )
                        self.rotate(-angle)

                    case "B":
                        self.board_widget.shoot(self.id)
                        self.board_widget.add_cmd_to_home_screen_cmd_history(
                            self.id, "B")

                    case "S":
                        if len(command) == 1:
                            self.board_widget.add_cmd_to_home_screen_cmd_history(
                                self.id, "S")
                            self.toggle_shield()

                        else:
                            if command[1] == "1":
                                self.board_widget.add_cmd_to_home_screen_cmd_history(
                                    self.id, "S1"
                                )
                                self.shield = True

                            elif command[1] == "0":
                                self.board_widget.add_cmd_to_home_screen_cmd_history(
                                    self.id, "S0"
                                )
                                self.shield = False

                            else:
                                command_ok = False

                    case _:
                        command_ok = False

        except (ValueError, IndexError, TypeError) as e:
            command_ok = False
            print(f">>>>> exception: {e}")

        # 3) Fallback UI note on invalid command
        if not command_ok:
            self.board_widget.add_llm_response_to_history(
                self.id, "[color=#FF0000][b]ERR[/b][/color]"
            )

        # 3b) Record parsed command and per-bot post-action state for compact history
        try:
            self.board_widget.history_manager.record_parsed_command(
                self.id, command if command_ok else ""
            )
            self.board_widget.history_manager.record_post_action_state(
                self.id, self.board_widget
            )

        except Exception:
            # Non-fatal: compact history will omit if not available
            pass

        # 4) Record assistant message in history
        self.board_widget.history_manager.record_message(
            self.id, "assistant", assistant_content
        )

        # 5) Finish turn
        self.ready_for_next_turn = True
        self.board_widget.on_bot_llm_interaction_complete(self)
