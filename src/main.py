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
from kivymd.app import MDApp
from kivy.config import Config
import os
os.environ["KIVY_NO_CONSOLELOG"] = "1"










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
        sm.add_widget(SettingsScreen(name="settings"))
        sm.add_widget(HistoryScreen(name="history"))

        self.icon = "assets/images/logo_small.png"  # TODO create an icon
        self.title = config.get("ui", "title")

        Window.bind(on_request_close=home.on_request_close)

        return sm

    def load_theme_colors(self):
        """
        Loads theme color definitions from a properties file and stores them in the `theme_colors` attribute.

        Reads the "theme_colors.properties" file line by line, ignoring empty lines and comments.
        For each valid line containing a key-value pair separated by '=', it parses the key and value,
        converts the value from a hex color string to a color object using `get_color_from_hex`, and
        stores the result in the `theme_colors` dictionary.

        Raises:
            FileNotFoundError: If the "theme_colors.properties" file does not exist.
            ValueError: If a line contains an invalid hex color value.
        """
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

        show_confirmation_dialog(
            "Exit Application", "Are you sure you want to exit?", on_confirm, on_cancel
        )
        return True


if __name__ == "__main__":
    Window.maximize()
    # os.environ["KIVY_NO_CONSOLELOG"] = "1"
    Config.set('kivy', 'log_level', 'error')
    Config.write()
    Window.maximize()
    BatLLM().run()
