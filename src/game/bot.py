"""
This module defines the `Bot` class, a Kivy Widget subclass that encapsulates the state and behavior of a game bot,
including graphical rendering, action execution, prompt history management, and LLM communication.
"""

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

from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.widget import Widget

from configs.app_config import config
from game.bullet import Bullet
from util.utils import markup


class Bot(Widget):
    """
    A game bot.
    """

    id = NumericProperty(0)
    x = NumericProperty(0.0)
    y = NumericProperty(0.0)
    rot = NumericProperty(0.0)  # degrees
    shield = ObjectProperty(None)
    health = NumericProperty(0)
    board_widget = ObjectProperty(None)  # The game board where the bot lives

    # Runtime state
    current_prompt: str | None = None
    prompt_history_index: int | None = None  # the index of the current prompt in the UI prompt storage
    ready_for_next_round: bool | None = None
    ready_for_next_turn: bool | None = None

    # LLM related
    last_llm_response: str | None = None



    def __init__(self, bot_id: int, board_widget, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.id = bot_id
        self.board_widget = board_widget

        self.ready_for_next_turn = False


        self.augmenting_prompt = bool(
            config.get("game", "prompt_augmentation"))

        self.independent_contexts = bool(
            config.get("game", "independent_contexts"))

        self.ready_for_next_turn = False

        # TODO colours load from theme properties
        if bot_id == 1:
            self.color = (0.8, 0.88, 1, 0.85)

        elif bot_id:
            self.color = (0.8, 0.65, 0.9, 0.85)

        else:
            self.color = (0, 1, 0, 1)

        # Bot properties from config
        self.diameter = float(config.get("game", "bot_diameter"))
        self.shield = bool(config.get("game", "shield_initial_state"))
        self.shield_range_deg = float(config.get("game", "shield_size"))
        self.health = int(config.get("game", "initial_health"))
        self.step = float(config.get("game", "step_length"))

        # Ramdom initial position and rotation
        self.x = random.uniform(0, 1)
        self.y = random.uniform(0, 1)
        self.rot = random.uniform(0, 359)  # degrees



    def render(self):
        """
        Renders the bot on the screen and a little info box next to it using graphical primitives.
        """

        r = (self.diameter or 0.1) / 2
        d = self.diameter or 0.1

        PushMatrix()
        Translate(self.x, self.y)
        Rotate(self.rot, 0, 0, 1)  # Gentle reminder, rot is in degrees

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


    # --Bot in-game actions
    def move(self):
        """
        One step for a bot...

        Returns:
            None
        """
        rad = math.radians(self.rot)
        self.x += (self.step or 0.02) * cos(rad)
        self.y += (self.step or 0.02) * sin(rad)


    def rotate(self, angle: float):
        """
        Rotates the object by a specified angle in degrees.

        Args:
            angle (float): The angle in degrees to rotate the object.
            Positive values rotate clockwise, negative values rotate counterclockwise.

        The rotation is normalized to stay within the range [0, 360) degrees.
        """
        self.rot = (self.rot + angle) % 360


    def damage(self):
        """
        Bot hit by a bullet, loses health.
        """
        self.health -= int(config.get("game", "bullet_damage"))
        self.health = max(self.health, 0)


    def toggle_shield(self):
        """
        Toggles the state of the shield.
        """
        self.shield = not self.shield


    def create_bullet(self):
        """
        A bot's way of shooting is to create a bullet and give it to the world to deal with.

        Returns:
            Bullet: A new Bullet instance initialized with the bot's id, position (x, y), and rotation (rot) if the shield is inactive.
            None: If the shield is active, no bullet is created and None is returned.
        """

        return Bullet(self.id, self.x, self.y, self.rot) if not self.shield else None




    @property
    def shield_range(self):
        """
        Returns the shield range as a float value.

        If the attribute 'shield_range_deg' is set, its value is converted to a float and returned.
        If 'shield_range_deg' is None or evaluates to False, 0.0 is returned.
        #TODO throw an exception if the shield_range_deg is not set. It's a required config value.

        Returns:
            float: The shield range in degrees.
        """
        return float(self.shield_range_deg or 0)

    # -- Prompt history - HomeScreen UI helpers
    def rewind_prompt_history(self):
        """
        Rewinds the bot's prompt history to the previous prompt in the UI prompt storage, if available.


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



    # LLM
    def submit_prompt_to_llm(self):
        # TODO implement this method to submit the current prompt to the LLM
        self.board_widget.ollama_connector.send_prompt_to_llm_sync(self.id, user_text=self.get_current_prompt())



    def get_current_prompt(self):
        return self.current_prompt or ""


    def _on_llm_response(self, res):
        """
        Handles the LLM response by parsing it, executing the command, recording history, and finishing the turn.

        Args:
            raw_response (str): The raw response from the LLM.

        """
        self.last_llm_response = res
        command_ok = True

        match res[0]:
            case "M":
                self.last_cmd = "M"
                self.move()

            case "C":
                angle = float(res[1:])  # if C, assume an angle follows and tries to parse it as a float
                self.last_cmd = f"C{angle}"

                self.rotate(angle)

            case "A":
                angle = float(res[1:])
                self.last_cmd = f"A{angle}"
                self.rotate(-angle)

            case "B":
                self.board_widget.shoot(self.id)
                self.last_cmd = "B"

            case "S":
                if len(res) == 1:
                    self.last_cmd = "S"
                    self.toggle_shield()

                else:
                    if res[1] == "1":
                        self.last_cmd = "S1"
                        self.shield = True

                    elif res[1] == "0":
                        self.last_cmd = "S0"
                        self.shield = False

                    else:
                        command_ok = False
                        self.last_cmd = "ERR"

            case _:
                command_ok = False
                self.last_cmd = "ERR"


        print(f"***** last_llm_response: {self.last_llm_response}")
        print(f"***** last_cmd: {self.last_cmd}")


        if not command_ok:
            color = "#FF0000"
            bold = True

        else:
            color = "#000000"
            bold = False


        self.board_widget.add_cmd_to_home_screen_cmd_history(self.id, markup(self.last_cmd, color=color, bold=bold))

        self.board_widget.history_manager.record_play(self)


        # Finish Play, let the board know we ready for the next turn.
        self.ready_for_next_turn = True
        self.board_widget.on_bot_llm_interaction_complete(self)
