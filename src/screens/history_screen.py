from kivy.properties import StringProperty, NumericProperty
from kivy.uix.screenmanager import Screen


class HistoryScreen(Screen):
    """
    Displays two scrolling histories via RecycleView:
      - rv_string_panel: the raw prompt log
      - rv_history_panel: the parsed/processed history
    """

  

    def update(self, bot_id: int, raw_prompt: str, parsed_history: str):
        """
        Populate both RecycleViews from the two input strings.

        Args:
            bot_id          -- the current bot's numeric id
            raw_prompt      -- the raw prompt text, newline‐separated
            parsed_history  -- the processed history, newline‐separated
        """
        self.current_bot_id = bot_id

        # split each on newlines and feed to rv.data
        raw_lines = raw_prompt.splitlines() or [""]
        parsed_lines = parsed_history.splitlines() or [""]

        # each item must be a dict matching the viewclass properties:
        self.ids.rv_string_panel.data = [{"text": line} for line in raw_lines]
        self.ids.rv_history_panel.data = [{"text": line} for line in parsed_lines]

    def go_back_home(self):
        self.manager.current = "home"
