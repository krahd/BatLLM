from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager

from screens.home_screen import HomeScreen
from screens.settings_screen import SettingsScreen

from kivy.core.window import Window


Builder.load_file("screens/settings_screen.kv")
Builder.load_file("screens/home_screen.kv")


class BattleLLM(App):
    
    def build(self):
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name = "home")) # starting screen
        sm.add_widget(SettingsScreen(name = "settings"))
        self.icon = "assets/checkbox_off.png" # TODO create an icon
        self.title = "BattLLM"
        return sm



if __name__ == "__main__":
    Window.maximize()
    BattleLLM().run()
    
    
    
