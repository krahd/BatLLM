import datetime
import sys

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen

from configs.app_config import config
from game.bot import Bot
# from game.game_board import GameBoard
from game.game_board import GameBoard
from game.history_manager import HistoryManager
from util.paths import prompt_asset_dir, resolve_saved_sessions_dir
from view.load_text_dialog import LoadTextDialog
from view.save_dialog import SaveDialog
from util.utils import show_confirmation_dialog, show_text_input_dialog, switch_screen


class HomeScreen(Screen):
    """
    A HomeScreen instance implements BotLLM's main screen.

    It contains the UX components for game control, prompting,
    and holds the GameBoard and a HistoryManager instance.

    """

    def __init__(self, **kwargs):
        """
        Constructor for the HomeScreen class.
        Initialises the screen and sets up the history manager.
        """
        super().__init__(**kwargs)
        self._exit_confirmation_popup = None


    def save_session(self):
        """
        Presents a confirmation prompt to the user to save the current game session.
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
                self._save_session_file(filename)
            else:
                pass

        def _on_saving_cancelled():
            """
            Do nothing if the user cancels the save prompt.
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
        Presents a confirmation prompt to the user to start a new game.
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
        switch_screen(self.manager, "settings", direction="left")


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
        switch_screen(self.manager, "history", direction="left")


    def save_prompt(self, bot_id):
        """
        Allows the user to save the content of the bot's prompt edition field to a file.

        Args:
            id (_type_): The bot id.
        """

        start_folder = str(prompt_asset_dir())
        ti = self.ids.get(f"prompt_input_{bot_id}")

        if not ti:
            return

        dlg = SaveDialog(content_to_save=ti.text, start_folder=start_folder)
        dlg.open()

    def set_prompt_history_text(self, bot_id, text):
        """
        Sets the content of the prompt history field for the specified bot id with the given text.

        Args:
            id (_type_): The bot id
            text (_type_): The prompt.

        """

        input_id = f"prompt_store_viewer_{bot_id}"
        self.ids.get(input_id).text = text


    def set_prompt_gui_input_text(self, bot_id, text):
        """
        Replaces the content of the prompt edition field for the specified bot id with the given text.


        Args:
            id (_type_): The bot  id
            text (_type_): The prompt.

        """

        input_id = f"prompt_input_{bot_id}"


        print(f"setting prompt input text for id {input_id} to: {text}")

        self.ids.get(input_id).text = text


    def get_prompt_gui_input_text(self, bot_id):
        """
        It returns the current state of the prompt edition field for the specified bot id.

        Args:
            id (_type_): The id.

        Returns:
            _type_: The text or an empty string if there's no bot with that id..
        """

        input_id = f"prompt_input_{bot_id}"
        text_input = self.ids.get(input_id)

        if text_input:
            return text_input.text

        return None


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


    def prompt_store_gui_set_text(self, bot_id, text):
        """
        Blindliy sets the content of the prompt store being shown in the guy.

        Args:
            id (_type_): bot id
            text (_type_): text to add to the prompts entered in the UI since the app started
        """

        input_id = f"prompt_store_viewer_{bot_id}"
        text_input = self.ids.get(input_id)

        if text_input:
            text_input.text = text


    def rewind_prompt_store(self, bot_id):
        """
        Selects the previous prompt in the bot's prompt history and sets it as the current prompt.

        Args:
            bot_id (_type_): the bot id
        """
        store = self.get_game_board().prompt_store

        print("********** CLICK ON REWIND PROMPT STORE FOR BOT", bot_id)

        new_prompt = (store.rewind(bot_id))
        print(f"New prompt: {new_prompt}")

        if (new_prompt is not None):
            self.prompt_store_gui_set_text(bot_id, new_prompt)

        else:
            print("**** EERR can't rewind prompt store any more :()")
            # TODO delete this print



    def forward_prompt_store(self, bot_id):
        """
        Selects the prenext  prompt in the bot's prompt history and sets it as the current prompt.

        Args:
            bot_id (_type_): The bot id
        """

        self.prompt_store_gui_set_text(bot_id, self.get_game_board().prompt_store.forward(bot_id))


    def retrieve_prompt_history_selected_text(self, bot_id):
        """
        Copies the selected prompt from the bot's prompt history to the editing area.

        Args:
            bot_id (_type_): The bot id.
        """




        # get the current prompt from the prompt store
        new_prompt = self.get_game_board().prompt_store.get_current_prompt(bot_id)
        # it should be the same than the one being shown in the prompt store viewer
        print("$$$$$$ new prompt:", new_prompt)

        #  set it as the current prompt being edited
        self.set_prompt_gui_input_text(bot_id, new_prompt)


    def submit_prompt_being_edited(self, bot_id):
        """
        Stores the text in the prompt edition field in the bot's prompt history and selects it.
        Flags the bot as ready to submit the prompt to its LLM.

        Args:
            bot_id (_type_): the bot id
        """

        new_prompt = self.get_prompt_gui_input_text(bot_id)

        if len(new_prompt) > 0:  # ignore empty prompts
            self.set_prompt_gui_input_text(bot_id, "")  # Clear the editing field
            self.set_prompt_history_text(bot_id, new_prompt)

            #  add the prompt to the store and to the bot
            gbw = self.ids.game_board
            gui_element_id = f"prompt_store_viewer_{bot_id}"

            gbw.prompt_store.add_prompt(bot_id, new_prompt)
            gbw.submit_prompt_to_bot(bot_id, new_prompt)



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
                input_id = f"prompt_input_{bot_id}"
                text_input = self.ids.get(input_id)
                text_input.text = text

        start_folder = str(prompt_asset_dir())
        dialog = LoadTextDialog(on_choice=file_dialog_callback, start_dir=start_folder)

        dialog.open()



    # --- events -----------------------
    def handle_window_key_down(self, _window, key, *_args):
        if key != 27:
            return False

        popup = getattr(self, "_exit_confirmation_popup", None)
        if popup is not None:
            self._exit_confirmation_popup = None
            cancel_action = getattr(popup, "cancel_action", None)
            if callable(cancel_action):
                cancel_action()
            else:
                popup.dismiss()
            return True

        return self.on_request_close()

    def on_request_close(self, *args, **kwargs):
        """
        Handles the request to close the application.
        Shows a confirmation prompt before closing.
        If the user confirms it offers to save the session to a file
        """

        def force_exit():
            """
            Exits the application.
            """

            App.get_running_app().stop()
            sys.exit(0)

        def _continue_exit_flow():
            """
            Continues with save-prompt handling or exits directly,
            depending on the UI configuration.
            """

            if not config.get("ui", "prompt_save_on_exit"):
                force_exit()
                return True

            def _on_filename_confirmed(filename):
                """
                Callback for the save confirmation prompt.
                If the user confirms, it offers to save the session to a file.
                """

                if filename:
                    self._save_session_file(filename)

                force_exit()

            def _on_filename_cancelled():
                """
                Exits the application without saving the session.
                """
                force_exit()

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            show_text_input_dialog(
                on_confirm=_on_filename_confirmed,
                on_cancel=_on_filename_cancelled,
                title="Save As",
                message="Please enter a filename or choose Don't Save\nto exit without saving.",
                default_text=f"session-{timestamp}.json",
                confirm_text="Save",
                cancel_text="Don't Save",
            )

            return True

        def _on_exit_cancelled():
            """
            Callback for the exit cancellation prompt.
            If the user cancels, it does nothing.
            """
            self._exit_confirmation_popup = None
            pass

        def _on_exit_confirmed():
            """
            Callback for the exit confirmation prompt.
            If the user confirms, it continues with the configured exit flow.
            """
            self._exit_confirmation_popup = None
            return _continue_exit_flow()

        if not config.get("ui", "confirm_on_exit"):
            _continue_exit_flow()
            return True

        self._exit_confirmation_popup = show_confirmation_dialog(
            title="Exit",
            message="Are you sure that you want to exit?",
            on_confirm=_on_exit_confirmed,
            on_cancel=_on_exit_cancelled,
        )
        return True


    def on_leave(self):
        Window.unbind(on_key_down=self.handle_window_key_down)


    def on_enter(self):
        """
        Called when the screen is entered.
        It initialises the GameBoard and Bot instances.
        """

        self.ids.overlay.darken = 0.2  # Set the initial overlay alpha value
        self.ids.overlay.desaturation = 0.1  # Set the initial desaturation value
        Window.unbind(on_key_down=self.handle_window_key_down)
        Window.bind(on_key_down=self.handle_window_key_down)

    def _save_session_file(self, filename: str) -> None:
        """Persist the current session into the configured save folder."""
        if not filename:
            return

        if not filename.lower().endswith(".json"):
            filename = f"{filename}.json"

        saved_sessions_folder = config.get("data", "saved_sessions_folder") or "saved_sessions"
        target_dir = resolve_saved_sessions_dir(saved_sessions_folder)
        target_path = target_dir / filename
        self.ids.game_board.history_manager.save_session(target_path)
