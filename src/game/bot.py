import math
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
from kivy.properties import NumericProperty, ObjectProperty  # type: ignore[import]
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
    independent_models: bool | None = None

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
        self.augmenting_prompt = bool(config.get("game", "prompt_augmentation"))
        self.independent_models = bool(config.get("game", "independent_models"))

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
        rad = math.radians(self.rot)
        self.x += (self.step or 0.02) * cos(rad)
        self.y += (self.step or 0.02) * sin(rad)

    def rotate(self, angle: float):
        self.rot = (self.rot + angle) % 360

    def damage(self):
        self.health -= int(config.get("game", "bullet_damage"))
        self.health = max(self.health, 0)

    def toggle_shield(self):
        self.shield = not self.shield

    def create_bullet(self):
        if not self.shield:
            return Bullet(self.id, self.x, self.y, self.rot)
        return None

    # Bullet helper compatibility
    def rot_rad(self):
        return math.radians(self.rot)

    @property
    def shield_range(self):
        return float(self.shield_range_deg or 0)

    # ------------------------- Prompt history (UI helpers) -------------------------
    def rewind_prompt_history(self):
        prompts = []
        hm = self.board_widget.history_manager
        if hm.current_round and "prompts" in hm.current_round:
            prompts = [p["prompt"] for p in hm.current_round["prompts"] if p.get("bot_id") == self.id]
        if self.prompt_history_index is None:
            if prompts:
                self.prompt_history_index = len(prompts) - 1
        else:
            if self.prompt_history_index > 0:
                self.prompt_history_index -= 1
        if self.prompt_history_index is not None and 0 <= self.prompt_history_index < len(prompts):
            self.current_prompt = prompts[self.prompt_history_index]

    def forward_prompt_history(self):
        prompts = []
        hm = self.board_widget.history_manager
        if hm.current_round and "prompts" in hm.current_round:
            prompts = [p["prompt"] for p in hm.current_round["prompts"] if p.get("bot_id") == self.id]
        if self.prompt_history_index is None:
            if prompts:
                self.prompt_history_index = 0
        else:
            if self.prompt_history_index < len(prompts) - 1:
                self.prompt_history_index += 1
        if self.prompt_history_index is not None and 0 <= self.prompt_history_index < len(prompts):
            self.current_prompt = prompts[self.prompt_history_index]

    def get_current_prompt_from_history(self):
        return self.current_prompt or ""

    def get_current_prompt(self):
        return self.get_current_prompt_from_history()

    def get_prompt(self):
        return self.get_current_prompt_from_history()

    def set_augmenting_prompt(self, augmenting: bool):
        self.augmenting_prompt = augmenting

    def get_augmenting_prompt(self):
        return bool(self.augmenting_prompt)

    def prepare_prompt_submission(self, new_prompt: str):
        self.current_prompt = new_prompt
        self.prompt_history_index = None
        self.ready_for_next_round = True

    # ------------------------- LLM communication -------------------------
    def submit_prompt_to_llm(self):
        """Build and send a chat request with: header, prompt(+state), and history."""
        # Refresh flags
        self.augmenting_prompt = bool(config.get("game", "prompt_augmentation"))
        self.independent_models = bool(config.get("game", "independent_models"))

        messages, user_content = self._build_chat_messages()
        # Record the user message for this turn
        self.board_widget.history_manager.record_message(self.id, "user", user_content)

        data = {
            "model": config.get("llm", "model"),
            "messages": messages,
            "stream": False,
        }

        base_url = config.get("llm", "url")
        port = config.get("llm", "port")
        path = config.get("llm", "path") or "/api/chat"
        chat_url = f"{base_url}:{port}{path}"

        self.board_widget.ollama_connector.send_request(
            chat_url,
            data,
            self._on_llm_response,
            self._on_llm_failure,
            self._on_llm_error,
        )

    def _get_mode_header_text(self) -> str:
        key = (
            "augmentation_header_independent"
            if self.independent_models
            else "augmentation_header_dependent"
        )
        path = config.get("llm", key)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            shared_fallback = os.path.join(os.path.dirname(path), "augmentation_header_shared_1.txt")
            try:
                with open(shared_fallback, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                return ""

    def _build_user_message_content(self) -> str:
        content = "PLAYER_INPUT:\n"
        content += (self.current_prompt or "") + "\n"
        if self.augmenting_prompt:
            content += "GAME_STATE:\n"
            content += f"Self.x: {self.x}, Self.y: {self.y}\n"
            content += f"Self.rot: {self.rot}\n"  # degrees
            content += f"Self.shield: {'ON' if self.shield else 'OFF'}\n"
            content += f"Self.health: {self.health}\n"
            opp = self.board_widget.get_bot_by_id(3 - self.id)
            if opp is not None:
                content += (
                    f"Opponent.x: {opp.x}, Opponent.y: {opp.y}\n"
                    f"Opponent.rot: {opp.rot}\n"
                    f"Opponent.shield: {'ON' if opp.shield else 'OFF'}\n"
                    f"Opponent.health: {opp.health}\n"
                )
        return content

    def _build_chat_messages(self) -> tuple[list[dict[str, str]], str]:
        system_message = {"role": "system", "content": self._get_mode_header_text()}
        if self.independent_models:
            history = self.board_widget.history_manager.get_chat_history(self.id, shared=False)
        else:
            history = self.board_widget.history_manager.get_chat_history(None, shared=True)
        user_content = self._build_user_message_content()
        user_message = {"role": "user", "content": user_content}
        messages: list[dict[str, str]] = [system_message]
        messages.extend(history)
        messages.append(user_message)
        return messages, user_content

    def _on_llm_failure(self, _request, _error):
        self.board_widget.on_bot_llm_interaction_complete(self)

    def _on_llm_error(self, _request, _error):
        self.board_widget.on_bot_llm_interaction_complete(self)

    def _on_llm_response(self, _req, result):
        """Parse the LLM reply, execute it, record history, and finish the turn."""
        # 1) Extract assistant content from common chat API shapes
        assistant_content = ""
        try:
            if isinstance(result, dict):
                if isinstance(result.get("response"), str):
                    assistant_content = result["response"]
                elif isinstance(result.get("message"), dict) and isinstance(result["message"].get("content"), str):
                    assistant_content = result["message"]["content"]
                elif isinstance(result.get("choices"), list) and result["choices"] and isinstance(result["choices"][0], dict):
                    choice = result["choices"][0]
                    msg = choice.get("message") if isinstance(choice, dict) else None
                    if isinstance(msg, dict) and isinstance(msg.get("content"), str):
                        assistant_content = msg["content"]
                elif isinstance(result.get("content"), str):
                    assistant_content = result["content"]
        except (TypeError, KeyError, ValueError):
            assistant_content = ""

        assistant_content = assistant_content.strip() if isinstance(assistant_content, str) else ""
        self.last_llm_response = assistant_content

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
                        self.board_widget.add_llm_response_to_history(self.id, "M")
                        self.move()
                    case "C":
                        angle = float(command[1:])
                        self.board_widget.add_llm_response_to_history(self.id, f"C{angle}")
                        self.rotate(angle)
                    case "A":
                        angle = float(command[1:])
                        self.board_widget.add_llm_response_to_history(self.id, f"A{angle}")
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
                                self.board_widget.add_llm_response_to_history(self.id, "S1")
                                self.shield = True
                            elif command[1] == "0":
                                self.board_widget.add_llm_response_to_history(self.id, "S0")
                                self.shield = False
                            else:
                                command_ok = False
                    case _:
                        command_ok = False
        except (ValueError, IndexError, TypeError) as e:
            command_ok = False
            print(f"exception: {e}")

        # 3) Fallback UI note on invalid command
        if not command_ok:
            self.board_widget.add_text_to_llm_response_history(
                self.id, "\n\n[color=#FF0000][b]Invalid Command.[/b][/color]\n\n"
            )
            self.board_widget.add_llm_response_to_history(self.id, "ERR")

        # 4) Record assistant message in history
        self.board_widget.history_manager.record_message(self.id, "assistant", assistant_content)

        # 5) Finish turn
        self.ready_for_next_turn = True
        self.board_widget.on_bot_llm_interaction_complete(self)
