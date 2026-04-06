"""Module HistoryScreen 
    """
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen
from util.utils import switch_screen

class HistoryScreen(Screen):
    """
    Displays two scrolling histories via RecycleView:
      - rv_string_panel: the raw prompt log
      - rv_history_panel: the parsed/processed history
    """

    def update(self, bot_id: int, raw_prompt: str, history: str):
        """
        Populate both RecycleViews in HistoryScreen using the strings passed as parameters.

        Args:
            bot_id          -- the current bot's numeric id
            raw_prompt      -- the raw prompt text, newline‐separated
            history         -- HistoryManager's to_text() output, newline‐separated
        """

        # Split on each newline, preserving empty items
        raw_lines = raw_prompt.split("\n")
        history_lines = history.split("\n")

        # build data lists
        self.ids.rv_string_panel.data = [{"text": line} for line in raw_lines]
        self.ids.rv_history_panel.data = [{"text": line} for line in history_lines]
        self.ids.title_label.text = f"History (Bot {bot_id})"

    def on_pre_enter(self, *_args):
        Window.unbind(on_key_down=self.handle_window_key_down)
        Window.bind(on_key_down=self.handle_window_key_down)

    def on_pre_leave(self, *_args):
        Window.unbind(on_key_down=self.handle_window_key_down)

    def handle_window_key_down(self, _window, key, *_args):
        if key != 27:
            return False

        self.go_back_home()
        return True


    def go_back_home(self):
        """
        Navigates back to the home screen by setting the current screen of the manager to "home".
        """
        switch_screen(self.manager, "home", direction="right")
