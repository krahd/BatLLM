import datetime
import os
import sys
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen

from configs.app_config import config
from game.bot import Bot
from game.game_board import GameBoard
from game.history_manager import HistoryManager
from util.load_text_dialog import LoadTextDialog
from util.save_dialog import SaveDialog
from util.utils import show_confirmation_dialog, show_text_input_dialog


class HomeScreen(Screen):
    """
    A HomeScreen instance implements BotLLM's main screen.

    It contains the UX components for game control, prompting,
    and holds the GameBoard and a HistoryManager instance.

    """

    def __init__(self, **kwargs):
        """
        Constructor for the HomeScreen class.
        Initializes the screen and sets up the history manager.
        """
        super().__init__(**kwargs)


    def save_session(self):
        """
        Presents a confirmation dialog to the user to save the current game session.
        If the user confirms, it saves the session to a file.
        If the user cancels, it does nothing.
        """

        def _on_saving_confirmed():
            """
            Proposes a timestamped filename to save the session.

            Returns:
                _type_: _description_
            """
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

            show_text_input_dialog(
                on_confirm=_on_filename_confirmed,
                title="Save as",
                message="Please enter a filename:",
                default_text=f"session-{timestamp}.json",
            )
            return True

        def _on_filename_confirmed(filename):
            """
            It asks the GameBoard to save the session to the specified filename.

            Args:
                filename (_type_): The filename to save the session to.
            """
            if filename:
                self.ids.game_board.save_session(filename)
            else:
                pass

        def _on_saving_cancelled():
            """
            Do nothing if the user cancels the saving dialog.
            """
            pass

        show_confirmation_dialog(
            "Save Session",
            "Are you sure you want to save the session?",
            _on_saving_confirmed,
            _on_saving_cancelled,
        )


    def start_new_game(self, force=False):
        """
        Presents a confirmation dialog to the user to start a new game.
        If the user confirms, it asks the GameBoard to start a new game.
        If the user cancels, it does nothing.
        """

        def _start_new_game():
            self.get_game_board().start_new_game()

        if not force:
            show_confirmation_dialog(
                "New Game", "Abandon current game and start a new one?", _start_new_game
            )
        else:
            _start_new_game()


    def get_game_board(self) -> GameBoard:
        """
        Returns the GameBoard instance.
        """
        return self.ids.game_board


    def go_to_settings_screen(self):
        """
        Handler for the settings button.
        Switches the current screen to the settings screen.
        """
        self.manager.current = "settings"


    def go_to_history_screen(self, bot_id):
        """
        Handler for the history buttons.
        Switches the current screen to the history screen and populates it.
        """
        gbw = self.ids.game_board
        history_screen = self.manager.get_screen("history")
        # Left pane: compact, per-bot summary
        compact = gbw.history_manager.to_compact_text_for_bot(int(bot_id))
        # Right pane: full detailed text for the whole game
        full_text = gbw.history_manager.to_text()
        history_screen.update(bot_id, compact, full_text)
        self.manager.current = "history"


    def save_prompt(self, bot_id):
        """
        Allows the user to save the content of the bot's prompt edition field to a file.

        Args:
            id (_type_): The bot id.
        """

        start_folder = os.path.join(os.getcwd(), "src", "assets", "prompts")
        ti = self.ids.get(f"prompt_player_{bot_id}")
        if not ti:
            return
        dlg = SaveDialog(content_to_save=ti.text, start_folder=start_folder)
        dlg.open()


    def set_prompt_input_text(self, bot_id, text):
        """
        Copies the text to the bot's prompt edition field.
        If the bot is not found, it does nothing.

        Args:
            id (_type_): The bot  id
            text (_type_): The prompt.

        """

        input_id = f"prompt_player_{bot_id}"
        text_input = self.ids.get(input_id)

        if text_input:
            text_input.text = text
        else:
            pass


    def get_prompt_input_text(self, bot_id):
        """
        It returns the current state of the prompt edition field for the specified bot id.

        Args:
            id (_type_): The id.

        Returns:
            _type_: The text or an empty string if there's no bot with that id..
        """

        input_id = f"prompt_player_{bot_id}"
        text_input = self.ids.get(input_id)

        if text_input:
            return text_input.text

        return ""


    def get_prompt_history_selected_text(self, bot_id):
        """
        Returns the text being edited by the prompt.

        Args:
            id (_type_): the bot id

        Returns:
            _type_: the text in the corresponding prompt text input
        """

        input_id = f"prompt_history_player_{bot_id}"
        text_input = self.ids.get(input_id)

        if text_input:
            return text_input.text
        else:
            print(f"No TextInput found for id: {input_id}")
            return ""


    def prompt_history_add_text(self, bot_id, text):
        """
        Stores the current state of the prompt being edited in the prompt
        history for the specified bot id.

        Args:
            id (_type_): bot id
            text (_type_): text to add to the prompts entered in the UI since the app started
        """

        input_id = f"prompt_history_player_{bot_id}"
        text_input = self.ids.get(input_id)

        if text_input:
            text_input.text = text


    def rewind_prompt_history(self, bot_id):
        """
        Selects the previous prompt in the bot's prompt history and sets it as the current prompt.

        Args:
            bot_id (_type_): the bot id
        """

        b = self.ids.game_board.get_bot_by_id(bot_id)
        b.rewind_prompt_history()
        self.prompt_history_add_text(bot_id, b.get_current_prompt_from_history())


    def forward_prompt_history(self, bot_id):
        """
        Selects the prenext  prompt in the bot's prompt history and sets it as the current prompt.

        Args:
            bot_id (_type_): The bot id
        """

        b = self.ids.game_board.get_bot_by_id(bot_id)
        b.forward_prompt_history()
        self.prompt_history_add_text(bot_id, b.get_current_prompt_from_history())


    def copy_prompt_history_selected_text(self, bot_id):
        """
        Copies the selected prompt from the bot's prompt history to the editing area.

        Args:
            bot_id (_type_): The bot id.
        """

        new_prompt = self.get_prompt_history_selected_text(bot_id)
        self.set_prompt_input_text(bot_id, new_prompt)


    def submit_prompt(self, bot_id):
        """
        Stores the text in the prompt edition field in the bot's prompt history and selects it.
        Flags the bot as ready to submit the prompt to its LLM.

        Args:
            bot_id (_type_): the bot id
        """

        new_prompt = self.get_prompt_input_text(bot_id)

        if len(new_prompt) > 0:  # ignore empty prompts
            # update the ui
            self.prompt_history_add_text(
                bot_id, new_prompt
            )  # copy the text to the prompt history
            self.set_prompt_input_text(bot_id, "")  # Clear the input field

            # tell the board to submit the prompt for this bot_id
            gbw = self.ids.game_board
            gbw.submit_prompt(bot_id, new_prompt)


    def load_prompt(self, bot_id):
        """
        Allows the user to select a file and loads its content into the bot's prompt edition field.

        Args:
            bot_id (_type_): the bot id
        """

        def file_dialog_callback(text):
            if text is None:
                # print("User cancelled")
                pass
            else:
                # print("Loaded text:\n", text[:200])  # first 200 chars
                input_id = f"prompt_player_{bot_id}"
                text_input = self.ids.get(input_id)
                text_input.text = text

        start_folder = os.path.join(os.getcwd(), "src", "assets", "prompts")
        dialog = LoadTextDialog(on_choice=file_dialog_callback, start_dir=start_folder)

        dialog.open()



    # --- events -----------------------
    def on_request_close(self, *args, **kwargs):
        """
        Handles the request to close the application.
        Shows a confirmation dialog before closing.
        If the user confirms it offers to save the session to a file
        """

        def _on_exit_cancelled():
            """
            Callback for the exit cancellation dialog.
            If the user cancels, it does nothing.
            """
            pass

        def _on_exit_confirmed():
            """
            Callback for the exit confirmation dialog.
            If the user confirms, it offers to save the session to a file.
            """

            def _on_filename_confirmed(filename):
                """
                Callback for the saving confirmation dialog.
                If the user confirms, it offers to save the session to a file.
                """

                if filename:
                    self.ids.game_board.save_session(filename)

                force_exit()

            def _on_filename_cancelled():
                """
                Exits the application without saving the session.
                """
                force_exit()

            def force_exit():
                """
                Exits the application.
                """

                App.get_running_app().stop()
                sys.exit(0)

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            show_text_input_dialog(
                on_confirm=_on_filename_confirmed,
                on_cancel=_on_filename_cancelled,
                title="Save As",
                message="Please enter a filename or cancel\nto exit without saving.",
                default_text=f"session-{timestamp}.json",
            )

            return True

        show_confirmation_dialog(
            title="Exit",
            message="Are you sure that you want to exit?",
            on_confirm=_on_exit_confirmed,
            on_cancel=_on_exit_cancelled,
        )
        return True



    def on_enter(self):
        """
        Called when the screen is entered.
        It initializes the GameBoard and Bot instances.
        """

        self.ids.overlay.darken = 0.2  # Set the initial overlay alpha value
        self.ids.overlay.desaturation = 0.1  # Set the initial desaturation value
