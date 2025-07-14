from kivy.app import App
from kivy.lang import Builder
from screens.home_screen import HomeScreen
from screens.settings_screen import SettingsScreen
from kivy.uix.screenmanager import ScreenManager

Builder.load_file("screens/settings_screen.kv")
Builder.load_file("screens/home_screen.kv")


class BattleLLM(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(SettingsScreen(name="settings"))
        sm.add_widget(HomeScreen(name="home")) # starting screen
      
        return sm

if __name__ == "__main__":
    BattleLLM().run()
