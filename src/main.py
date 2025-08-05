from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
from kivy.properties import DictProperty
from kivy.utils import get_color_from_hex
from screens.home_screen import HomeScreen
from screens.settings_screen import SettingsScreen
from screens.history_screen import HistoryScreen
from configs.app_config import config
from util.utils import show_confirmation_dialog
import sys



Builder.load_file("screens/settings_screen.kv")
Builder.load_file("screens/home_screen.kv")
Builder.load_file("screens/history_screen.kv")


class BatLLM(MDApp):
    """This is the main application class for BattLLM.
    Using Kivy, it initializes the screen manager and sets up the application's windows
    
    Args:
        App (_type_): Kivy's base application class.

    Attributes:
        theme_colors (DictProperty): A dictionary to hold theme colors loaded from a properties file.   
    """    
    theme_colors = DictProperty({})  # Expose to KV

    def build(self):                        
        sm = ScreenManager()

        home = HomeScreen(name="home")
        
        sm.add_widget(home)
        sm.add_widget(SettingsScreen(name = "settings"))    
        sm.add_widget(HistoryScreen(name = "history"))               
        
        self.icon = "assets/images/logo_small.png" # TODO create an icon
        self.title = config.get("ui", "title") 
        
        Window.bind(on_request_close=home.on_request_close)

        return sm

    def load_theme_colors(self):
        self.theme_colors = {}
        with open("theme_colors.properties", "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    self.theme_colors[key.strip()] = get_color_from_hex(value.strip())


    def on_request_close(self, *args, **kwargs):
        """Handles the request to close the application.
        Prompts the user to confirm if they want to exit.
        """
        def on_confirm():
            self.stop()
            sys.exit()

        def on_cancel():
            pass

        show_confirmation_dialog("Exit Application",
                                 "Are you sure you want to exit?",
                                 on_confirm, on_cancel)
        return True
    

if __name__ == "__main__":
    Window.maximize()
    BatLLM().run()
    
