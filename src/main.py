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
        sm.add_widget(HomeScreen(name = "home"))          # starting screen
        sm.add_widget(SettingsScreen(name = "settings"))
        
        #TODO create a new screen to show the round being played, animated, with the result of each prompt rendered, with a timeline where the players can go back and forth in the game

        
        self.icon = "assets/checkbox_off.png" # TODO create an icon
        self.title = "BattLLM" # TODO add version from config
        
        return sm



if __name__ == "__main__":
    Window.maximize()
    BattleLLM().run()
    
    
    
