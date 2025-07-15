from kivy.uix.screenmanager import Screen
from pathlib import Path

class HomeScreen(Screen):
    pass

    def save_game (self):
        print ("Saving game...")

    def go_to_settings_screen(self):
        self.manager.current = "settings"

    def on_kv_post(self, base_widget):
        prompt_path = Path(__file__).parent / "../assets/prompts/prompt_2.txt"
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.ids.prompt_history_player_1.text = f.read()
        except FileNotFoundError:
            self.ids.prompt_history_player_1.text = "[Error: prompt file not found]"


    def render_game(self):
        game_board_widget = self.ids.game_board_widget
        if hasattr(game_board_widget, 'render'):
            game_board_widget.render()
        else:
            print("GameBoardWidget does not have a render method.")