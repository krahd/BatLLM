import os
import sys

from kivy.config import Config
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import DictProperty
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.utils import get_color_from_hex
from kivymd.app import MDApp

os.environ["KIVY_NO_CONSOLELOG"] = "1"
MIN_PYTHON = (3, 10)


def require_supported_python() -> None:
    """Exit early with a clear message on unsupported Python versions."""
    if sys.version_info >= MIN_PYTHON:
        return
    version = ".".join(str(part) for part in sys.version_info[:3])
    raise SystemExit(f"BatLLM requires Python 3.10 or newer. Detected Python {version}.")


require_supported_python()

from configs.app_config import config
from util.paths import asset_path, register_kivy_resource_paths, repo_path, theme_colors_path, view_path
from util.utils import show_confirmation_dialog
from view.history_screen import HistoryScreen
from view.home_screen import HomeScreen
from view.ollama_config_screen import OllamaConfigScreen
from view.settings_screen import SettingsScreen

register_kivy_resource_paths()

Builder.load_file(str(view_path("settings_screen.kv")))
Builder.load_file(str(view_path("home_screen.kv")))
Builder.load_file(str(view_path("history_screen.kv")))
Builder.load_file(str(view_path("ollama_config_screen.kv")))


class BatLLM(MDApp):
    """This is the main application class for BattLLM.
    Using Kivy, it initialises the screen manager and sets up the application's windows

    Args:
        App (_type_): Kivy's base application class.

    Attributes:
        theme_colors (DictProperty): A dictionary to hold theme colours loaded from a properties file.
    """

    theme_colors = DictProperty({})  # Expose to KV

    def build(self):
        sm = ScreenManager(transition=SlideTransition(direction="left"))

        home = HomeScreen(name="home")

        sm.add_widget(home)
        sm.add_widget(SettingsScreen(name="settings"))
        sm.add_widget(HistoryScreen(name="history"))
        sm.add_widget(OllamaConfigScreen(name="ollama_config"))

        icon_candidates = (
            asset_path("images", "logo_small.png"),
            repo_path("docs", "images", "logo-small.png"),
        )
        for icon_path in icon_candidates:
            if icon_path.exists():
                self.icon = str(icon_path)
                break
        self.title = config.get("ui", "title")

        Window.bind(on_request_close=home.on_request_close)

        return sm

    def load_theme_colors(self):
        """
        Loads theme colour definitions from a properties file and stores them in the `theme_colors` attribute.

        Reads the "theme_colors.properties" file line by line, ignoring empty lines and comments.
        For each valid line containing a key-value pair separated by '=', it parses the key and value,
        converts the value from a hex colour string to a colour object using `get_color_from_hex`, and
        stores the result in the `theme_colors` dictionary.

        Raises:
            FileNotFoundError: If the "theme_colors.properties" file does not exist.
            ValueError: If a line contains an invalid hex colour value.
        """
        self.theme_colors = {}
        with theme_colors_path().open("r", encoding="utf-8") as f:
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


def main() -> int:
    require_supported_python()
    Config.set("kivy", "log_level", "error")
    Config.write()
    if hasattr(Window, "maximize"):
        Window.maximize()
    BatLLM().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
