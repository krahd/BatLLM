from kivy.uix.screenmanager import Screen


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

        print ("****")
        print (f"history_lines: {history_lines}")
        print ("****")
        print ("****")


        # build data lists
        self.ids.rv_string_panel.data = [{"text": line} for line in raw_lines]
        self.ids.rv_history_panel.data = [{"text": line} for line in history_lines]

        self.ids.title_label.text = f"[b]History for Bot {bot_id}[/b]"


        
    def go_back_home(self):
        self.manager.current = "home"
