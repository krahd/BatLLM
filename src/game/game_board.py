"""
game_board.py
===============

The :mod:`game_board` module contains the :class:`~game.game_board.GameBoard`
class which implements BatLLM's in-game logic and user interface. It acts
as the "world" in which bots act, and it mediates communication between bots,
the LLM via :class:`~game.ollama_connector.OllamaConnector`,
and the :class:`~game.history_manager.HistoryManager` which records all game
state and chat history.

Key features:
- Maintains a list of :class:`~game.bot.Bot` instances representing the players. Bots are created at the start of each game.
- Coordinates the flow of games, rounds and turns, and updates ``current_turn`` and ``current_round`` counters accordingly.
- Renders the game graphics using Kivy and updates various UI labels.
- Provides helper methods to append text to scrollable history boxes in the HomeScreen (see ``add_text_to_llm_response_history``).
- Uses the HistoryManager as the single source of truth for all chat messages.
- Chat messages are recorded via ``HistoryManager.record_message`` and reconstructed with ``HistoryManager.get_chat_history``.
- At the end of each round, the board logs status text directly through ``add_text_to_llm_response_history``.

The GameBoard drives the game loop and delegates state recording to the HistoryManager.
The UI updates are handled through a small set of helper methods.
"""

import os
import random
import sys

from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.event import EventDispatcher
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.properties import NumericProperty
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget

from configs.app_config import config
from game.bot import Bot
from game.history_manager import HistoryManager
from util.normalized_canvas import NormalizedCanvas
from util.utils import find_id_in_parents, markup, show_fading_alert
from game.ollama_connector import OllamaConnector  # TODO move to singleton


class GameBoard(Widget, EventDispatcher):
    """
    The GameBoard is BatLLM's game world and a Kivy Widget.
    Attributes:
        bots (list): List of Bot instances participating in the game.
        bullet_trace (list): List of bullet positions for rendering bullet traces.
        bullet_alpha (float): Alpha value for bullet trace fading effect.
        sound_shoot (Sound): Sound effect for shooting.
        sound_bot_hit (Sound): Sound effect for bot hit.
        current_turn (NumericProperty): Current turn number within the round.
        current_round (NumericProperty): Current round number within the game.
        games_started (NumericProperty): Number of games started in the session.
        shuffled_bots (list): List of bots in randomized order for turn-taking.
        history_manager (HistoryManager): Manages chat and game history.

    Methods:
        __init__(**kwargs): Initializes the GameBoard, sets up input, rendering, and state.
        on_current_turn(instance, value): Updates UI when the turn changes.
        on_current_round(instance, value): Updates UI when the round changes.
        on_games_started(instance, value): Updates UI when a new game starts.
        start_new_game(): Resets state and starts a new game.
        save_session(filename): Saves the current session via the HistoryManager.
        on_kv_post(base_widget): Called after KV rules are applied; starts a new game.
        _keyboard_closed(): Handles virtual keyboard closure.
        _redraw(*args): Triggers a redraw of the game board.
        render(*args): Draws the current game state.
        on_touch_down(touch): Handles mouse/touch input for focus.
        on_touch_move(touch): Handles mouse drag events (unused).
        add_text_to_home_screen_cmd_history(bot_id, text): Appends text to the bot's output history in the UI.
        add_cmd_to_home_screen_cmd_history(bot_id, command): Appends parsed LLM command to the UI.
        submit_prompt_to_game(bot_id, new_prompt): Handles prompt submission and round progression.
        game_is_over(): Checks if the game has ended.
        play_turn(dt): Executes a single turn and manages round/turn transitions.
        end_game(): Ends the game and displays results.
        update_title_label(): Updates the UI label with current game/round/turn info.
        on_bot_llm_interaction_complete(bot): Callback after a bot completes LLM interaction.
        get_bot_by_id(bot_id): Retrieves a bot by its ID.
        snapshot(): Returns a snapshot of the current bot states.
        _on_keyboard_down(keyboard, keycode, text, modifiers): Handles keyboard input for debugging/testing.
        shoot(bot_id): Handles shooting logic for a bot.
        _grab_keyboard(): Requests keyboard focus for the widget.
        _on_keyboard_closed(): Cleans up keyboard bindings on closure.
    """


    bots = []
    bullet_trace = []
    bullet_alpha = 1
    sound_shoot = None
    sound_bot_hit = None
    current_turn = NumericProperty(0)  # Start with turn 0
    current_round = NumericProperty(0)  # Start with round 0
    # Count of games started in this session
    games_started = NumericProperty(0)
    shuffled_bots = None
    history_manager = None


    def __init__(self, **kwargs):
        """
        Constructor. Initializes the GameBoard instance and
        schedules the render loop to update the UI at the configured frame rate.
        """

        super(GameBoard, self).__init__(**kwargs)

        self._keyboard = Window.request_keyboard(
            self._keyboard_closed, self, "text")
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

        self.bind(size=self._redraw, pos=self._redraw)

        self.bullet_trace = []  # Initialize bullet trace list
        self.bullet_alpha = 1  # Initialize bullet alpha value

        self.sound_shoot = SoundLoader.load("assets/sounds/shoot1.wav")
        self.sound_bot_hit = SoundLoader.load("assets/sounds/bot_hit.wav")

        self.current_turn = 0
        self.current_round = 0
        self.games_started = 0
        self.shuffled_bots = None

        self.history_manager = HistoryManager()  # Create the session history manager

        # Create the connector responsible for LLM communication
        self.ollama_connector = OllamaConnector()


        # Render loop
        Clock.schedule_interval(
            self._redraw, 1.0 / config.get("ui", "frame_rate"))


    def on_current_turn(self, instance, value):
        """Callback for current_turn property change.
        It updates the title label with the new turn information.

        Args:
                instance (_type_): The instance of the GameBoard.
                value (_type_): The new value of the current_turn property.
        """
        self.update_title_label()


    def on_current_round(self, instance, value):
        """Callback for current_round property change.
        It updates the title label with the new round information.

        Args:
                instance (_type_): The instance of the GameBoard.
                value (_type_): The new value of the current_round property.
        """
        self.update_title_label()


    def on_games_started(self, instance, value):
        """
        Callback triggered when the `games_started` property changes.

        This method updates the title label to reflect the new number of games started.

            instance: The instance of the GameBoard where the property changed.
            value: The new value of the `games_started` property.

        started property.
        """
        self.update_title_label()


    def start_new_game(self):
        """
        Starts a new game by resetting game state and initializing bots.
        - Notifies the history manager to start tracking the new game.

        Returns:
            None
        """

        # reset values
        self.current_turn = 0
        self.current_round = 0
        self.shuffled_bots = None

        # Create two bot instances with reference to this GameBoard
        self.bots = [Bot(bot_id=i, board_widget=self) for i in range(1, 3)]

        if self.games_started > 0:
            for b in self.bots:
                self.add_text_to_home_screen_cmd_history(
                    b.id, "[b][color=#f00000]\n\nNew Game\n\n[/color][/b]"
                )
                b.ready_for_next_round = False  # need a new prompt for a new round

        self.games_started += 1
        self.history_manager.start_game(self)

    # TODO check / test / implement save and load session
    def save_session(self, filename):
        """Upon user confirmation it asks the HistoryManager to save all the session information recorded until this moment.

        Args:
                filename (_type_): the name of the json file.
        """
        folder = f"{config.get('data', 'saved_sessions_folder')}"
        os.makedirs(folder, exist_ok=True)

        filepath = os.path.join(folder, filename)
        print("saving session to", filepath)
        self.history_manager.save_session(filepath)
        print("done")


    def on_kv_post(self, base_widget):
        """This method is called after the KV rules have been applied

        Args:
                base_widget (_type_): The root of the tree of elements to check
        """
        super().on_kv_post(base_widget)

        Clock.schedule_once(
            lambda dt: self.start_new_game(), 0
        )  # Start a new game after the KV rules have been applied


    def _keyboard_closed(self):
        """virtual keyboard closed handler. Unbinds the listener."""

        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None


    def _redraw(self, *args):
        """Refreshes the screen by calling render()"""
        # TODO check this
        self.render()
        #  Clock.schedule_once(self.render())
        # We don't need to schedule it because _redraw itself is scheduled with Clodk.schedule_interval to begin with


    def render(self, *args):
        """Draws the game world in its current state.
        It uses a NormalizedCanvas for drawing.
        """
        # TODO improve the game graphics

        # Clear the canvas before drawing
        self.canvas.clear()

        # keep bots inside bounds
        for bot in self.bots:
            r = bot.diameter / 2

            if bot.x < r:
                bot.x = r
            elif bot.x > 1 - r:
                bot.x = 1 - r

            if bot.y < r:
                bot.y = r
            elif bot.y > 1 - r:
                bot.y = 1 - r

        with NormalizedCanvas(self):
            c = 1
            Color(c, c, c, 1)
            Rectangle(pos=(0, 0), size=(1, 1))
            c = 0.2
            Color(c, c, c, 0.6)
            Line(rectangle=(0, 0, 1, 1), width=0.001)

            for bot in self.bots:
                bot.render()

            for x, y in self.bullet_trace:
                # Red color for bullet trace # TODO make it configurable from theme
                Color(1, 0, 0, self.bullet_alpha)
                Ellipse(pos=(x - 0.005, y - 0.005), size=(0.005, 0.005))

                if self.bullet_alpha > 0:
                    self.bullet_alpha -= 0.0015  # Decrease alpha for fading effect
                else:
                    self.bullet_trace.clear()


    def on_touch_down(self, touch):
        """
        If the gameboard is clicked on, it grabs the keyboard focus.

        Args:
                touch (_type_): touch event

        Returns:
                _type_: True iff the event has been handled
        """

        if self.collide_point(touch.x, touch.y):
            nx, ny = NormalizedCanvas.to(self, touch.x, touch.y)
            self._grab_keyboard()  # get the keyboard back
            return True

        return super().on_touch_down(touch)


    def on_touch_move(self, touch):
        """Mouse drag event handler. Not used.
        Args:
                touch (_type_): touch event

        Returns:
                _type_: True iff the event has been handled
        """

        if self.collide_point(touch.x, touch.y):
            nx, ny = NormalizedCanvas.to(self, touch.x, touch.y)
            return True

        return super().on_touch_move(touch)


    def add_text_to_home_screen_cmd_history(self, bot_id, text):
        """
        Adds the text to the output history box next to the bot's prompt input.

        Args:
                bot_id (_type_): bot id
                text (_type_): text to add
        """

        box = find_id_in_parents(self, f"output_history_player_{bot_id}")

        if box is not None:
            box.text += text

            scroll = find_id_in_parents(
                self, f"scroll_output_history_player_{bot_id}")

            lbl = find_id_in_parents(self, f"output_history_player_{bot_id}")
            n_lines = lbl.text.count("\n")

            if (
                n_lines > 20
            ):  # After the first 20 liines, we scroll to the bottom every time we add a new line
                Clock.schedule_once(setattr(scroll, "scroll_y", 0))
        else:
            print(
                f"ERROR: Could not find output history box for bot_id: {bot_id}")


    def add_cmd_to_home_screen_cmd_history(self, bot_id, command):
        """
        Appends the result of parsing the llm's response to the
        scrollable label in the home_screen that each player has

        Args:
                bot_id (_type_): bot id
                command (_type_): correct llm responses parse into commands
        """
        text = f"[color=#000000]{command}[/color]\n"
        self.add_text_to_home_screen_cmd_history(bot_id, text)


    def submit_prompt_to_history_gui(self, bot_id, new_prompt):
        """Tells the bot with bot_id to submit its promt for the coming round.
        If both bots have submitted, it starts the next turn.

        Args:
                bot_id (_type_): the bot id
                new_prompt (_type_): the player's prompt
        """

        # Record the new prompt for the specified bot.
        bot = self.get_bot_by_id(bot_id)
        bot.prepare_prompt_submission(new_prompt)

        # Only start a new round when all bots have provided a prompt.
        # If not everyone is ready yet, simply return and wait for the other bot.
        if not all(b.ready_for_next_round for b in self.bots):
            return

        # Both bots are ready, so start a new round.
        # Reset the turn counter and increment the round counter.
        if self.current_round is None:
            self.current_round = 0
            self.current_turn = 0

        self.current_round += 1
        self.current_turn += 1

        # TODO check this
        # Notify players via the output history and reset the ready flags.
        for b in self.bots:
            self.add_text_to_home_screen_cmd_history(b.id, markup(
                f"Round {self.current_round}\n", font_size=18, bold=True))
            b.ready_for_next_round = False

        # Randomise the order of playing turns. Use the number of bots to sample all of them.
        self.shuffled_bots = random.sample(self.bots, len(self.bots))

        # Tell the history manager that a new round is starting.
        self.history_manager.start_round(self)

        # Begin the first turn of the round. `play_turn` will call start_turn
        # internally and handle scheduling subsequent turns.

        Clock.schedule_once(self.play_turn)


    def game_is_over(self):
        """Checks if the game is over.

        Returns:
                _type_: true iff the game is over
        """

        for b in self.bots:
            if b.health <= 0:
                return True

        if self.current_round >= config.get("game", "total_rounds"):
            return True

        return False


    def play_turn(self, dt):
        """Executes one turn.
        The game logic is implemented recursively,

        Args:
            dt (_type_): Time since last call. Kivy passes dt automatically to any callback scheduled with CLock.
        """

        if not self.current_turn < config.get("game", "turns_per_round"):
            # round's over
            self.history_manager.end_round()
            self.current_turn = 0  # Reset turn counter for the next round


            for b in self.bots:
                # Insert blank line to separate rounds in the UI.
                self.add_text_to_home_screen_cmd_history(b.id, "\n\n")
                # Directly log the end of the round to the UI
                # using the GameBoard's helper to append text.
                self.add_text_to_home_screen_cmd_history(b.id,
                                                         markup(f"Round {self.current_round} ended.",
                                                                color="#a00000", bold=True)
                                                         )


            round_res = "\n"  # Collects round results to display in the popup.

            if self.game_is_over():
                self.end_game()
                self.start_new_game()

            else:
                for b in self.bots:
                    round_res += f"Bot {b.id}'s health: {b.health}\n\n"

                show_fading_alert(
                    f"Round {self.current_round} is over",
                    round_res,
                    duration=1,
                    fade_duration=0.8,
                )

            return

        # If the round is not over, we start a turn and submit each bot's prompt to the LLM.
        self.update_title_label()
        self.history_manager.start_turn(self)

        for b in self.bots:
            # Reset the bot's ready_for_next_turn flag for the new turn.
            b.ready_for_next_turn = False


        # Submission go in this round's shuffled order.
        for b in self.shuffled_bots:
            b.submit_prompt_to_llm()




    def end_game(self):
        """
        Ends the game and displays the final results.
        """

        self.history_manager.end_game(self)

        round_res = "Final Results:\n\n"
        for b in self.bots:
            round_res += f"Bot {b.id}'s health: {b.health}\n"

        popup = Popup(
            title="Game Over",
            content=Label(text=round_res),
            size_hint=(None, None),
            size=(470, 460),
        )
        popup.open()



    def update_title_label(self):
        """Updates the label above the game board with the current game, round and turn information."""
        game_title_label = find_id_in_parents(self, "game_title_label")
        if game_title_label is not None:
            game_title_label.text = f"[size=30]   Game {self.games_started}"

            if self.current_round is not None:
                game_title_label.text += " > "
                game_title_label.text += f"Round {self.current_round}"

                if self.current_turn is not None:
                    game_title_label.text += " > "
                    game_title_label.text += f"Turn {self.current_turn}."

            game_title_label.text += "[/size]"



    def on_bot_llm_interaction_complete(self, bot):
        """Callback method executed after a prompt-response cycle has been completed by a bot
        if all bots are ready for the next turn yt ends the turn and schedules the next one

        Args:
                bot (_type_): the bot
        """
        # Record the bot's play in the history manager.
        self.history_manager.record_play(bot)

        # if all bots are done, end turn and schedule the next one
        if all(b.ready_for_next_turn for b in self.bots):
            self.current_turn += 1
            self.history_manager.end_turn(self)
            Clock.schedule_once(self.play_turn)




    def get_bot_by_id(self, bot_id: int):
        """Returns the bot instance with the specified ID.

        Args:
                bot_id (_type_): The bot with the id or None if not found.
        """
        for b in self.bots:
            if getattr(b, "id", None) == bot_id:
                return b
        return None



    def snapshot(self) -> dict[int, dict]:
        return {
            b.id: {"x": b.x, "y": b.y, "rot": b.rot,
                   "health": b.health, "shield": int(bool(b.shield))}
            for b in self.bots
        }



    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """Keyboard handler for the game board. It is used for debug and testing purposes alone.
        Once the codebase is more mature it should be conditional on the debug flag.

        Args:
                keyboard (_type_): type of keyboard
                keycode (_type_): the code of the pressed key
                text (_type_): the symbol correspnding to the key
                modifiers (_type_): the modifiers being pressed (shift, command, etc).

        Returns:
                _type_: True
        """

        if modifiers and "shift" in modifiers:
            bot_id = 2
        else:
            bot_id = 1

        bot = self.get_bot_by_id(bot_id)

        if keycode[1] == "escape":
            keyboard.release()

        else:
            match keycode[1]:
                case "m":
                    bot.move()

                case "r":
                    bot.rotate(10)

                case "t":
                    bot.rotate(-10)

                case "s":
                    bot.toggle_shield()

                case "b":
                    self.shoot(bot.id)

                case "q":
                    sys.exit(0)

                case "l":
                    # TODO load a prompt to both fields and submit them so that it starts a new round to make testing easier
                    pass

            return True



    def shoot(self, bot_id):
        """A bullet is shot by a bot.
        Args:
                bot_id (_type_): "The id of the bot that shoots."
        """
        bot = self.get_bot_by_id(bot_id)
        bullet = bot.create_bullet()
        self.bullet_alpha = 1
        bullet_is_alive = True
        damaged_bot_id = None

        if bullet is not None:
            Clock.schedule_once(self.sound_shoot.play())
        else:
            bullet_is_alive = False

        while bullet_is_alive:
            (bullet_is_alive, damaged_bot_id) = bullet.update(self.bots)

            # only draw the bullet when it is outside the bot that fires it
            dist = ((bullet.x - bot.x) ** 2 + (bullet.y - bot.y) ** 2) ** 0.5

            if dist * 0.97 > bot.diameter / 2:
                # TODO check this
                Clock.schedule_once(self.bullet_trace.append((bullet.x, bullet.y)))

        if damaged_bot_id is not None:
            Clock.schedule_once(self.sound_bot_hit.play())

            self.get_bot_by_id(damaged_bot_id).damage()

            if self.game_is_over():
                self.end_game()
                self.start_new_game()



    def _grab_keyboard(self):
        """Request the keyboard and bind our handler."""
        if self._keyboard is None:
            self._keyboard = Window.request_keyboard(
                self._on_keyboard_closed,  # called if user cancels
                self,  # target widget
                "text",  # input type
            )
            if self._keyboard:
                self._keyboard.bind(on_key_down=self._on_keyboard_down)



    def _on_keyboard_closed(self):
        """Unbind and drop reference when keyboard is released."""
        if self._keyboard:
            self._keyboard.unbind(on_key_down=self._on_keyboard_down)
            self._keyboard = None



    def get_game_state(self) -> dict:
        """Returns the current game state as a dictionary.
        This includes bot positions, health, and other relevant data.

        Returns:
            dict: A dictionary representing the current game state.
        """
        return {
            "bots": self.snapshot(),
            "current_turn": self.current_turn,
            "current_round": self.current_round,
            "bullet_trace": self.bullet_trace,
            "bullet_alpha": self.bullet_alpha,
        }
        # TODO Add any other game state information as needed
