"""
game_board.py
===============

The :mod:`game_board` module contains the :class:`~game.game_board.GameBoard`
class, which implements BatLLM's in-game logic and user interface. It acts
as the "world" in which bots act, and mediates communication between bots,
the LLM via :class:`~game.ollama_connector.OllamaConnector`,
and the :class:`~game.history_manager.HistoryManager`, which records all game
state and chat history.

Key features:
- Maintains a list of :class:`~game.bot.Bot` instances representing the players.
- Coordinates the flow of games, rounds and turns, and updates counters.
- Renders the game graphics using Kivy and updates various UI labels.
- Provides helpers to append text to scrollable history boxes in the HomeScreen.
- Uses HistoryManager as the single source of truth for chat messages.
- Chat messages are recorded via HistoryManager and reconstructed on demand.
- At the end of each round, the board logs status text through the UI helper.

The GameBoard drives the game loop and delegates state recording to the
HistoryManager. UI updates are handled through a small set of helper methods.
"""

from __future__ import annotations

import os
import random
import sys
from typing import Optional, Tuple

from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget

from configs.app_config import config
from game.bot import Bot
from game.history_manager import HistoryManager
from game.ollama_connector import LLMTimeoutError, OllamaConnector  # TODO move to singleton
from game.prompt_store import PromptStore
from game.replay_engine import GameplaySettingsSnapshot, resolve_shot
from util.paths import asset_path
from util.utils import (
    find_id_in_parents,
    markup,
    show_fading_alert,
    show_text_input_dialog,
)
from view.normalized_canvas import NormalizedCanvas


class GameBoard(Widget):
    """
    The GameBoard is BatLLM's game world and a Kivy Widget.
    It manages game state (bots, turns, rounds), rendering, and UI hooks.
    """

    # NumericProperties should remain class attributes (Kivy pattern)
    current_turn = NumericProperty(0)   # Start with turn 0
    current_round = NumericProperty(0)  # Start with round 0
    games_started = NumericProperty(0)  # Count of games started in this session

    def __init__(self, **kwargs):
        """
        Constructor. Initializes the GameBoard instance and schedules the
        render loop to update the UI at the configured frame rate.
        """
        super().__init__(**kwargs)

        # Instance state (avoid class-level mutable defaults)
        self.bots: list[Bot] = []
        self.prompt_store: Optional[PromptStore] = PromptStore()
        self.bullet_trace: list[Tuple[float, float]] = []
        self.bullet_alpha: float = 1.0  # only one bullet can be shot at a time
        self.bullet = None
        self.shuffled_bots: Optional[list[Bot]] = None
        self.current_round_settings: Optional[GameplaySettingsSnapshot] = None
        self._turn_submission_queue: list[Bot] = []
        self._turn_submission_index: int = 0
        self._round_timeout_action: str | None = None
        self._timeout_popup: Optional[Popup] = None

        # Audio
        self.sound_shoot = SoundLoader.load(str(asset_path("sounds", "shoot1.wav")))
        self.sound_bot_hit = SoundLoader.load(str(asset_path("sounds", "bot_hit.wav")))

        # History + LLM connector
        self.history_manager = HistoryManager()
        self.ollama_connector = OllamaConnector()

        # Keyboard handling
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self, "text")
        if self._keyboard:
            self._keyboard.bind(on_key_down=self._on_keyboard_down)

        # Redraw on size/pos updates
        self.bind(size=self._redraw, pos=self._redraw)

        # Render loop
        fps = float(config.get("ui", "frame_rate"))
        Clock.schedule_interval(self._redraw, 1.0 / fps)

    # -------------------------------------------------------------------------
    # Kivy property callbacks
    # -------------------------------------------------------------------------

    def on_current_turn(self, instance, value):
        """Update title label when current turn changes."""
        self.update_title_label()

    def on_current_round(self, instance, value):
        """Update title label when current round changes."""
        self.update_title_label()

    def on_games_started(self, instance, value):
        """Update title label when number of games started changes."""
        self.update_title_label()

    # -------------------------------------------------------------------------
    # Game lifecycle
    # -------------------------------------------------------------------------

    def start_new_game(self):
        """
        Starts a new game by resetting game state and initializing bots.
        Notifies the history manager to start tracking the new game.
        """
        # Reset counters for the new game
        self.current_turn = 0
        self.current_round = 0
        self.shuffled_bots = None
        self.current_round_settings = None
        self._turn_submission_queue = []
        self._turn_submission_index = 0
        self._round_timeout_action = None
        self._timeout_popup = None

        # Create two bots with reference to this GameBoard
        self.bots = [Bot(bot_id=i, board_widget=self) for i in range(1, 3)]

        # Initialize a fresh prompt store
        self.prompt_store = PromptStore()

        # If not the first game, log "New Game"
        if self.games_started > 0:
            for b in self.bots:
                self.add_text_to_home_screen_cmd_history(
                    b.id, "[b][color=#f00000]\n\nNew Game\n\n[/color][/b]"
                )
                # Require new prompts for a new round
                b.ready_for_next_round = False

        self.games_started += 1
        self.history_manager.start_game(self)

    def end_game(self):
        """Ends the game and displays the final results."""
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

    def game_is_over(self) -> bool:
        """Return True iff the game is over."""
        for b in self.bots:
            if b.health <= 0:
                return True

        rules = self.current_round_settings or GameplaySettingsSnapshot.from_config()
        total_rounds = int(rules.total_rounds)
        if self.current_round >= total_rounds:
            return True

        return False

    # -------------------------------------------------------------------------
    # KV lifecyle hooks
    # -------------------------------------------------------------------------

    def on_kv_post(self, base_widget):
        """Called after the KV rules have been applied."""
        super().on_kv_post(base_widget)
        # Start a new game once widgets are ready
        Clock.schedule_once(lambda dt: self.start_new_game(), 0)

    # -------------------------------------------------------------------------
    # Keyboard handling
    # -------------------------------------------------------------------------

    def _keyboard_closed(self):
        """Virtual keyboard closed handler. Unbinds the listener."""
        if self._keyboard:
            self._keyboard.unbind(on_key_down=self._on_keyboard_down)
            self._keyboard = None

    def _grab_keyboard(self):
        """Request the keyboard and bind our handler."""
        if self._keyboard is None:
            self._keyboard = Window.request_keyboard(
                self._keyboard_closed,  # called if user cancels
                self,                   # target widget
                "text",                 # input type
            )
            if self._keyboard:
                self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """
        Keyboard handler for the game board. For debug and testing purposes.
        """
        # Shift selects bot 2, otherwise bot 1
        bot_id = 2 if (modifiers and "shift" in modifiers) else 1
        bot = self.get_bot_by_id(bot_id)

        if keycode[1] == "escape":
            keyboard.release()
            return True

        if not bot:
            print(f"ERROR: Bot {bot_id} not found.")
            return True

        match keycode[1]:
            case "c":
                self._prompt_manual_command(bot)
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
                # Example submission for testing
                for i in range(2):
                    self.submit_prompt_being_edited(
                        i,
                        (
                            "If you are looking towards your opponent and your shield is up, return S\n"
                            "If you are looking towards your opponent and your shield is down, return B\n"
                            "If you are not looking towards your opponent rotate to face your opponent"
                        ),
                    )

        return True

    # -------------------------------------------------------------------------
    # Input events
    # -------------------------------------------------------------------------

    def _prompt_manual_command(self, bot: Bot) -> None:
        """
        Show a popup to collect a manual command for the selected bot and execute it.
        """

        def _dispatch(command: str) -> None:
            bot.process_llm_response(command.strip().upper())

        show_text_input_dialog(
            on_confirm=_dispatch,
            title=f"Bot {bot.id} Command",
            message="Enter a command (e.g. M, M0.2, C20, A15, S, S1, S0, B).",
            input_hint="Command",
        )

    def on_touch_down(self, touch):
        """
        If the gameboard is clicked on, it grabs the keyboard focus.
        """
        if self.collide_point(touch.x, touch.y):
            _nx, _ny = NormalizedCanvas.to(self, touch.x, touch.y)
            self._grab_keyboard()
            return True
        return super().on_touch_down(touch)



    def on_touch_move(self, touch):
        """Mouse drag handler (currently unused)."""
        if self.collide_point(touch.x, touch.y):
            _nx, _ny = NormalizedCanvas.to(self, touch.x, touch.y)
            return True
        return super().on_touch_move(touch)

    # -------------------------------------------------------------------------
    # Rendering
    # -------------------------------------------------------------------------

    def _redraw(self, *args):
        """Refresh the screen by calling render()."""
        self.render()

    def render(self, *args):
        """Draw the game world in its current state using a NormalizedCanvas."""
        # Clear the canvas before drawing
        self.canvas.clear()

        # Keep bots inside bounds
        for bot in self.bots:
            r = bot.diameter / 2
            bot.x = min(max(bot.x, r), 1 - r)
            bot.y = min(max(bot.y, r), 1 - r)

        with NormalizedCanvas(self):
            # Background
            c = 1.0
            Color(c, c, c, 1)
            Rectangle(pos=(0, 0), size=(1, 1))

            # Border
            c = 0.2
            Color(c, c, c, 0.6)
            Line(rectangle=(0, 0, 1, 1), width=0.001)

            # Bots
            for bot in self.bots:
                bot.render()


            # Bullet trace (alpha fading managed outside the draw loop)
            # We don't use bullet.render, instead we handle bullet rendering here
            for x, y in self.bullet_trace:
                Color(1, 0, 0, self.bullet_alpha)  # TODO: theme color
                Ellipse(pos=(x - 0.005, y - 0.005), size=(0.005, 0.005))


        # Fade effect: reduce alpha and clear when fully faded
        if self.bullet is None:
            if self.bullet_trace:
                self.bullet_alpha = max(0.0, self.bullet_alpha - 0.025)
                if self.bullet_alpha == 0.0:
                    self.bullet_trace.clear()


    # -------------------------------------------------------------------------
    # UI helpers
    # -------------------------------------------------------------------------

    def add_text_to_home_screen_cmd_history(self, bot_id: int, text: str):
        """
        Adds text to the output history box next to the bot's prompt input.
        """
        box = find_id_in_parents(self, f"output_history_player_{bot_id}")
        if box is None:
            print(f"ERROR: Could not find output history box for bot_id: {bot_id}")
            return

        box.text += text

        scroll = find_id_in_parents(self, f"scroll_output_history_player_{bot_id}")
        lbl = find_id_in_parents(self, f"output_history_player_{bot_id}")
        if not scroll or not lbl:
            return

        n_lines = lbl.text.count("\n")
        # After the first 20 lines, auto-scroll to bottom on append
        if n_lines > 20:
            Clock.schedule_once(lambda dt: setattr(scroll, "scroll_y", 0))

    def add_cmd_to_home_screen_cmd_history(self, bot_id: int, command: str):
        """
        Appends the result of parsing the LLM's response to the scrollable label.
        """
        text = f"[color=#000000]{command}[/color]\n"
        self.add_text_to_home_screen_cmd_history(bot_id, text)

    # -------------------------------------------------------------------------
    # Prompts & rounds
    # -------------------------------------------------------------------------

    def submit_prompt_to_bot(self, bot_id: int, new_prompt: str):
        """
        Register the player's prompt for the coming round.
        If all bots have submitted, start the next turn (and round if needed).
        """
        bot = self.get_bot_by_id(bot_id)
        if not bot:
            print(f"ERROR: bot {bot_id} not found")
            return

        # Record the new prompt for the specified bot (and optionally in PromptStore)
        bot.current_prompt = new_prompt
        bot.ready_for_next_round = True
        if self.prompt_store:
            self.prompt_store.add_prompt(bot_id, new_prompt)

        # If not everyone is ready yet, wait for the other bot
        if not all(b.ready_for_next_round for b in self.bots):
            return

        # All bots are ready → start a new round (the moment bots receive new prompts)
        if self.current_round is None:
            self.current_round = 0
            self.current_turn = 0

        self.current_round += 1
        self.current_turn = 0  # reset per-round turn counter
        self._turn_submission_queue = []
        self._turn_submission_index = 0
        self._round_timeout_action = None
        first_round_of_game = bool(
            self.history_manager.current_game) and not self.history_manager.current_game.get("rounds")
        self.current_round_settings = GameplaySettingsSnapshot.from_config()
        self._apply_round_settings_to_live_bots(
            self.current_round_settings,
            reset_for_new_game=first_round_of_game,
        )

        # Announce round start and reset per-bot flags
        for b in self.bots:
            self.add_text_to_home_screen_cmd_history(
                b.id, markup(f"Round {self.current_round}\n", font_size=18, bold=True)
            )
            b.ready_for_next_round = False
            b.ready_for_next_turn = False

        # Randomize the order of playing turns
        self.shuffled_bots = random.sample(self.bots, len(self.bots))

        # Tell the history manager a new round is starting, then kick the first turn
        self.history_manager.start_round(self)
        Clock.schedule_once(self.play_turn)

    def _apply_round_settings_to_live_bots(
        self,
        rules: GameplaySettingsSnapshot,
        *,
        reset_for_new_game: bool,
    ) -> None:
        """Freeze round-level gameplay settings onto the live bot widgets."""
        for bot in self.bots:
            bot.diameter = rules.bot_diameter
            bot.default_step = rules.bot_step_length
            bot.shield_range_deg = rules.shield_size
            if reset_for_new_game:
                bot.health = rules.initial_health
                bot.shield = rules.shield_initial_state



    def play_turn(self, dt):
        """Executes one turn. Game logic advances frame-by-frame via Kivy's Clock. TODO: does it?"""
        rules = self.current_round_settings or GameplaySettingsSnapshot.from_config()
        turns_per_round = int(rules.turns_per_round)

        if not self.current_turn < turns_per_round:
            # Round ended
            self._turn_submission_queue = []
            self._turn_submission_index = 0
            self._round_timeout_action = None
            self.history_manager.end_round()
            # Insert visual separation and summary
            for b in self.bots:
                self.add_text_to_home_screen_cmd_history(b.id, "\n\n")
                self.add_text_to_home_screen_cmd_history(
                    b.id, markup(f"Round {self.current_round} ended.", color="#a00000", bold=True)
                )

            if self.game_is_over():
                self.end_game()
                self.start_new_game()
                return

            # Show round results popup
            round_res = "\n"
            for b in self.bots:
                round_res += f"Bot {b.id}'s health: {b.health}\n\n"

            show_fading_alert(
                f"Round {self.current_round} is over",
                round_res,
                duration=1,
                fade_duration=0.8,
            )
            return

        # Round is not over → start a turn
        self.update_title_label()
        self.history_manager.start_turn(self)

        # Reset the per-turn readiness
        for b in self.bots:
            b.ready_for_next_turn = False

        # Submission goes in the shuffled order
        self._turn_submission_queue = list(self.shuffled_bots or self.bots)
        self._turn_submission_index = 0
        self._submit_next_bot_for_turn()




    def on_bot_llm_interaction_complete(self, bot: Bot):
        """
        Callback executed after a prompt-response cycle completes for a bot.
        If all bots are ready for the next turn, end the turn and schedule the next one.
        """
        # Record the bot's play in the history manager
        self.history_manager.record_play(bot)

        # If all bots are done, end turn and schedule next
        if all(b.ready_for_next_turn for b in self.bots):
            self.current_turn += 1
            self.history_manager.end_turn(self)
            Clock.schedule_once(self.play_turn)
            return

        self._submit_next_bot_for_turn()

    def _submit_next_bot_for_turn(self):
        """Submit the next bot in the current turn order, if any remain."""
        if self._turn_submission_index >= len(self._turn_submission_queue):
            return
        bot = self._turn_submission_queue[self._turn_submission_index]
        self._turn_submission_index += 1
        bot.submit_prompt_to_llm()

    def _clear_timeout_popup(self, *_args):
        self._timeout_popup = None

    def _dismiss_timeout_popup_and_resolve(
        self,
        bot: Bot,
        exc: LLMTimeoutError,
        *,
        action: str,
        remember_for_round: bool,
    ):
        popup = self._timeout_popup
        if popup is not None:
            popup.dismiss()
        self._resolve_bot_timeout(
            bot,
            exc,
            action=action,
            remember_for_round=remember_for_round,
        )

    def _format_timeout_message(self, bot: Bot, exc: LLMTimeoutError) -> str:
        timeout_suffix = f" after {exc.timeout:g}s" if exc.timeout is not None else ""
        model_name = exc.model or self.ollama_connector.model or "the selected model"
        return (
            f"Bot {bot.id} timed out waiting for {model_name}{timeout_suffix}. "
            f"BatLLM already retried once."
        )

    def handle_bot_llm_timeout(self, bot: Bot, exc: LLMTimeoutError):
        """Resolve an LLM timeout using the round policy or a user choice popup."""
        if self._round_timeout_action == "err":
            self._resolve_bot_timeout(bot, exc, action="err", remember_for_round=False)
            return

        if self._round_timeout_action == "cancel":
            self._resolve_bot_timeout(bot, exc, action="cancel", remember_for_round=False)
            return

        self._show_timeout_resolution_popup(bot, exc)

    def _resolve_bot_timeout(
        self,
        bot: Bot,
        exc: LLMTimeoutError,
        *,
        action: str,
        remember_for_round: bool,
    ):
        """Apply the user's timeout choice to the current round."""
        if remember_for_round:
            self._round_timeout_action = action

        timeout_message = self._format_timeout_message(bot, exc)

        if action == "err":
            self.add_text_to_home_screen_cmd_history(
                bot.id,
                markup("Timeout after retry -> ERR\n", color="#a00000", bold=True),
            )
            bot.finish_turn_with_error(timeout_message)
            return

        if action == "cancel":
            self.cancel_current_round(bot, timeout_message)
            return

        raise ValueError(f"Unknown timeout action: {action}")

    def _show_timeout_resolution_popup(self, bot: Bot, exc: LLMTimeoutError):
        """Ask the user whether a timed out bot should resolve as ERR or cancel the round."""
        if self._timeout_popup is not None:
            self._timeout_popup.dismiss()

        remember_checkbox = CheckBox(active=False, size_hint=(None, None), size=(36, 36))
        message_label = Label(
            text=self._format_timeout_message(
                bot, exc) + "\n\nChoose how BatLLM should resolve this timeout.",
            halign="left",
            valign="middle",
        )
        message_label.bind(size=lambda instance, size: setattr(
            instance, "text_size", (size[0], None)))

        remember_label = Label(
            text="Use this choice for the rest of the round",
            halign="left",
            valign="middle",
        )
        remember_label.bind(size=lambda instance, size: setattr(
            instance, "text_size", (size[0], None)))

        checkbox_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=44, spacing=10)
        checkbox_row.add_widget(remember_checkbox)
        checkbox_row.add_widget(remember_label)

        button_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=48, spacing=10)
        err_button = Button(text="Use ERR")
        cancel_button = Button(text="Cancel Round")
        button_row.add_widget(err_button)
        button_row.add_widget(cancel_button)

        content = BoxLayout(orientation="vertical", padding=12, spacing=12)
        content.add_widget(message_label)
        content.add_widget(checkbox_row)
        content.add_widget(button_row)

        popup = Popup(
            title="Ollama Timeout",
            content=content,
            size_hint=(None, None),
            size=(560, 320),
            auto_dismiss=False,
        )
        popup.bind(on_dismiss=self._clear_timeout_popup)

        err_button.bind(
            on_release=lambda *_args: self._dismiss_timeout_popup_and_resolve(
                bot,
                exc,
                action="err",
                remember_for_round=bool(remember_checkbox.active),
            )
        )
        cancel_button.bind(
            on_release=lambda *_args: self._dismiss_timeout_popup_and_resolve(
                bot,
                exc,
                action="cancel",
                remember_for_round=bool(remember_checkbox.active),
            )
        )

        self._timeout_popup = popup
        popup.open()

    def _restore_round_initial_state(self):
        """Roll back live bot state to the round-start snapshot."""
        if not self.history_manager.current_round:
            return

        initial_state = self.history_manager.current_round.get("initial_state", {})
        for bot in self.bots:
            bot_state = initial_state.get(bot.id)
            if not bot_state:
                continue
            bot.health = bot_state.get("health", bot.health)
            bot.x = bot_state.get("x", bot.x)
            bot.y = bot_state.get("y", bot.y)
            bot.rot = bot_state.get("rot", bot.rot)
            bot.shield = bot_state.get("shield", bot.shield)
            bot.current_prompt = bot_state.get("current_prompt", bot.current_prompt)
            bot.last_llm_response = bot_state.get("last_llm_response")

        self.bullet = None
        self.bullet_trace.clear()
        self.bullet_alpha = 1.0

    def cancel_current_round(self, bot: Bot, reason: str):
        """Cancel the active round, roll back state, and keep a cancelled-round history entry."""
        round_number = self.current_round
        self._restore_round_initial_state()
        self.history_manager.cancel_round(reason, cancelled_by_bot_id=bot.id)
        self._turn_submission_queue = []
        self._turn_submission_index = 0
        self._round_timeout_action = None
        self.current_turn = 0
        self.current_round_settings = None

        for current_bot in self.bots:
            current_bot.ready_for_next_round = False
            current_bot.ready_for_next_turn = False
            self.add_text_to_home_screen_cmd_history(current_bot.id, "\n")
            self.add_text_to_home_screen_cmd_history(
                current_bot.id,
                markup(f"Round {round_number} cancelled.", color="#a00000", bold=True),
            )
            self.add_text_to_home_screen_cmd_history(current_bot.id, "\n")

        if self.game_is_over():
            self.end_game()
            self.start_new_game()
            return

        show_fading_alert(
            f"Round {round_number} cancelled",
            reason,
            duration=1.4,
            fade_duration=1.0,
        )



    # -------------------------------------------------------------------------
    # Shooting & bullets
    # -------------------------------------------------------------------------

    def shoot(self, bot_id: int):
        """
        Shoot a bullet from the given bot. Bullet updates are scheduled on the Clock for animation
        to avoid blocking the UI thread.
        """
        bot = self.get_bot_by_id(bot_id)
        if not bot:
            print(f"ERROR: bot {bot_id} not found")
            return

        self.bullet_alpha = 1.0
        rules = self.current_round_settings or GameplaySettingsSnapshot.from_config()
        shot = resolve_shot(self.snapshot(), bot_id, rules)
        if shot.reason == "no_shot":
            return

        self.bullet = None
        self.bullet_trace = list(shot.path)

        if self.sound_shoot and shot.path:
            self.sound_shoot.play()

        if shot.damaged_bot_id is not None:
            if self.sound_bot_hit:
                self.sound_bot_hit.play()
            target = self.get_bot_by_id(shot.damaged_bot_id)
            if target:
                target.damage(amount=rules.bullet_damage)
            if self.game_is_over():
                self.end_game()
                self.start_new_game()



    # -------------------------------------------------------------------------
    # Title & state
    # -------------------------------------------------------------------------

    def update_title_label(self):
        """Update the label above the game board with current game/round/turn info."""
        game_title_label = find_id_in_parents(self, "game_title_label")
        if not game_title_label:
            return

        parts = [f"Game {self.games_started}"]
        parts.append(f"Round {self.current_round}")
        parts.append(f"Turn {self.current_turn}")
        game_title_label.text = "[size=30]   " + " > ".join(parts) + "[/size]"



    def get_bot_by_id(self, bot_id: int) -> Optional[Bot]:
        """Return the bot instance with the specified ID, or None if not found."""
        for b in self.bots:
            if getattr(b, "id", None) == bot_id:
                return b
        return None



    def snapshot(self) -> dict[int, dict]:
        """Lightweight snapshot of bot state for UI/state dumps."""
        return {
            b.id: {
                "x": b.x,
                "y": b.y,
                "rot": b.rot,
                "health": b.health,
                "shield": int(bool(b.shield)),
            }
            for b in self.bots
        }




    def get_game_state(self) -> dict:
        """
        Returns the current game state as a dictionary:
        bot positions/health, current turn/round, and bullet trace/alpha.
        """
        return {
            "bots": self.snapshot(),
            "current_turn": self.current_turn,
            "current_round": self.current_round,
            # TODO check if bulllet should be added (if existant)
        }



    # -------------------------------------------------------------------------
    # Testing & debugging
    # -------------------------------------------------------------------------

    def submit_prompt_being_edited(self, bot_id: int, text: str):
        """
        Example helper used in keyboard testing path; route text to LLM or UI.
        Replace with your actual handler if different.
        """
        self.submit_prompt_to_bot(bot_id, text)
