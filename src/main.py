from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from screens.home_screen import HomeScreen
from widgets.game_board import GameBoardWidget
from screens.settings_screen import SettingsScreen


Builder.load_file("screens/settings_screen.kv")
Builder.load_file("screens/home_screen.kv")


class BattleLLM(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home")) # starting screen
        sm.add_widget(SettingsScreen(name="settings"))
        return sm

if __name__ == "__main__":
    BattleLLM().run()
