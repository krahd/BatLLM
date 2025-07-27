from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window

from screens.home_screen import HomeScreen
from screens.settings_screen import SettingsScreen

from configs.app_config import config

Builder.load_file("screens/settings_screen.kv")
Builder.load_file("screens/home_screen.kv")


class BattLLM(App):
    """This is the main application class for BattLLM.
    Using Kivy, it initializes the screen manager and sets up the application's windows
    
    Args:
        App (_type_): Kivy's base application class.
    """    
  
    def build(self):        
        Builder.load_file("screens/home_screen.kv")
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name = "home"))  # starting screen        
        sm.add_widget(SettingsScreen(name = "settings"))        
        
        self.icon = "assets/logo_small.png" # TODO create an icon
        self.title = config.get("ui", "title") 
        
        return sm


if __name__ == "__main__":
    Window.maximize()
    BattLLM().run()
    
    
    
