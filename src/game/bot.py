import json
import math
import random
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
from kivy.network.urlrequest import UrlRequest
from kivy.properties import NumericProperty, ObjectProperty  # type: ignore[import]
from kivy.uix.widget import Widget

from configs.app_config import config
from game.bullet import Bullet
from util.normalized_canvas import NormalizedCanvas


class Bot(Widget):
    """This class models a game bot.

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

    prompt_history = None
    prompt_history_index = None
    ready_for_next_round = None
    ready_for_next_turn = None
    agmenting_prompt = None

    llm_endpoint = None
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
        self.prompt_history = []
        self.prompt_history_index = 0
        self.board_widget = board_widget
        self.ready_for_next_round = False
        self.ready_for_next_turn = False
        self.agmenting_prompt = config.get("game", "prompt_augmentation")

        if bot_id == 1:
            self.color = (0.8, 0.88, 1, 0.85)
        elif bot_id:
            self.color = (0.8, 0.65, 0.9, 0.85)
        else:
            self.color = (0, 1, 0, 1)

        port_base = config.get("llm", "port_base")

        if not config.get("game", "independent_models"):
            port = f"{port_base + 1}"
            # shared model for both bots in 5001.
            # TODO change it to a third LLM listening in port_base

        else:
            port = f"{port_base + bot_id}"  # ports 5001, 5002, etc. for each bot

        self.llm_endpoint = (
            config.get("llm", "url") + ":" + port + config.get("llm", "path")
        )

        self.diameter = config.get("game", "bot_diameter")
        self.shield = config.get("game", "shield_initial_state")
        self.shield_range_deg = config.get("game", "shield_size")
        self.health = config.get("game", "initial_health")
        self.step = config.get("game", "step_length")

        # Randomly initialize position and rotation of each bot
        self.x = random.uniform(0, 1)
        self.y = random.uniform(0, 1)
        self.rot = random.uniform(0, 359)

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

        t = "x: {:.3f}\ny: {:.3f}\nrot: {:1.2f}r / {:3.0f}d\nshield: {}\nhealth: {}".format(
            self.x,
            self.y,
            self.rot,
            math.degrees(self.rot),
            "ON" if self.shield else "OFF",
            self.health,
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
        """Adds the new prompt to the prompt.history object.
        It is now ready to run it.

        Args:
            new_prompt (_type_): the new prompt
        """
        self.prompt_history.append(new_prompt)
        self.prompt_history_index = len(self.prompt_history) - 1

    def rewind_prompt_history(self):
        """Rewinds"""
        if self.prompt_history_index is not None and self.prompt_history_index > 0:
            self.prompt_history_index -= 1
            # print(f"Rewound to prompt: {self.prompt_history_index}")

    def forward_prompt_history(self):
        """Forwards"""
        if (
            self.prompt_history_index is not None
            and self.prompt_history_index < len(self.prompt_history) - 1
        ):
            self.prompt_history_index += 1
            # print(f"Forwarded to prompt: {self.prompt_history_index}")

    def get_current_prompt_from_history(self):
        """Returns a prompt from the history using a cursor. Rewind and Forward move the cursor.

        Returns:
            _type_: a string with the prompt
        """
        res = ""
        try:
            res = self.prompt_history[self.prompt_history_index]
        except (IndexError, TypeError):
            res = ""

        return res

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

    def augmenting_prompt(self, augmenting):
        """Toggles the flag indicating if the player prompts are augmented with game info.

        Args:
            augmenting (_type_): the new flag value
        """
        self.agmenting_prompt = augmenting

    def prepare_prompt_submission(self, new_prompt):
        """Gets ready to execute

        Args:
            new_prompt (_type_): the prompt to use
        """
        self.append_prompt_to_history(new_prompt)
        self.ready_for_next_round = True

    def submit_prompt_to_llm(self):
        """Takes care of the interaction with the LLM"""
        headers = {"Content-Type": "application/json"}

        data = {
            "model": "llama3.2:latest",  # TODO get this from config or from game board
            "prompt": "",
            "stream": False,  # TODO get this from config
        }

        # We augment the prompt if the flag is set
        if config.get("game", "prompt_augmentation"):

            # To facilitate exploration and testing, we allow the header file to be changed on the fly, so we reload prompt_augmentation_header just in case
            file = open(
                config.get("llm", "augmentation_header_file"), "r", encoding="utf-8"
            )
            hdr = file.read()

            file.close()
            data["prompt"] = hdr
            data["prompt"] += "GAME_STATE:\n"
            data["prompt"] += f"Self.x: {self.x}, Self.y: {self.y}\n"
            data["prompt"] += f"Self.rot: {math.degrees(self.rot)}\n"
            data["prompt"] += f"Self.shield: {'ON' if self.shield else 'OFF'}\n"
            data["prompt"] += f"Self.health: {self.health}\n"
            data[
                "prompt"
            ] += f"Opponent.x: {self.board_widget.get_bot_by_id(3 - self.id).x}, Opponent.y: {self.board_widget.get_bot_by_id(3 - self.id).y}\n"
            data[
                "prompt"
            ] += f"Opponent.rot: {math.degrees(self.board_widget.get_bot_by_id(3 - self.id).rot)}\n"
            data[
                "prompt"
            ] += f"Opponent.shield: {'ON' if self.board_widget.get_bot_by_id(3 - self.id).shield else 'OFF'}\n"
            data[
                "prompt"
            ] += f"Opponent.health: {self.board_widget.get_bot_by_id(3 - self.id).health}\n"
            data["prompt"] += "PLAYER_INPUT:\n"

        data["prompt"] += self.get_current_prompt() + "\n"

        UrlRequest(
            url=self.llm_endpoint,
            req_body=json.dumps(data),
            req_headers=headers,
            on_success=self._on_llm_response,
            on_failure=self._on_llm_failure,  # HTTP errors 4xx, 5xx
            on_error=self._on_llm_error,  # other errors (no connection, etc.)
            timeout=30,
            method="POST",
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

        self.last_llm_response = result.get("response", "").strip()

        cmd = self.last_llm_response

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
