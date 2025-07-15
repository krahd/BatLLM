from kivy.app import App
from kivy.lang import Builder
from screens.home_screen import HomeScreen
from screens.settings_screen import SettingsScreen
from kivy.uix.screenmanager import ScreenManager
from widgets.game_board import GameBoardWidget 

Builder.load_file("screens/settings_screen.kv")
Builder.load_file("screens/home_screen.kv")


class BattleLLM(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home")) # starting screen
        sm.add_widget(SettingsScreen(name="settings"))
        game_board_widget = GameBoardWidget()
        
      
        return sm

if __name__ == "__main__":
    BattleLLM().run()
