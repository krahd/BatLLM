import os
import sys
import threading

from kivy.config import Config
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import DictProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.utils import get_color_from_hex
from kivymd.app import MDApp

import ollama_service

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
from util.utils import show_confirmation_dialog, show_fading_alert
from util.version import current_app_version
from view.analyzer_load_screen import AnalyzerLoadScreen
from view.analyzer_review_screen import AnalyzerReviewScreen
from view.history_screen import HistoryScreen
from view.home_screen import HomeScreen
from view.ollama_config_screen import OllamaConfigScreen
from view.settings_screen import SettingsScreen

register_kivy_resource_paths()

Builder.load_file(str(view_path("settings_screen.kv")))
Builder.load_file(str(view_path("home_screen.kv")))
Builder.load_file(str(view_path("history_screen.kv")))
Builder.load_file(str(view_path("ollama_config_screen.kv")))
Builder.load_file(str(view_path("analyzer_load_screen.kv")))
Builder.load_file(str(view_path("analyzer_review_screen.kv")))


class BatLLM(MDApp):
    """This is the main application class for BattLLM.
    Using Kivy, it initialises the screen manager and sets up the application's windows

    Args:
        App (_type_): Kivy's base application class.

    Attributes:
        theme_colors (DictProperty): A dictionary to hold theme colours loaded from a properties file.
    """

    theme_colors = DictProperty({})  # Expose to KV
    app_version = StringProperty(current_app_version())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._startup_ollama_flow_completed = False

    def build(self):
        sm = ScreenManager(transition=SlideTransition(direction="left"))

        home = HomeScreen(name="home")

        sm.add_widget(home)
        sm.add_widget(SettingsScreen(name="settings"))
        sm.add_widget(HistoryScreen(name="history"))
        sm.add_widget(OllamaConfigScreen(name="ollama_config"))
        sm.add_widget(AnalyzerLoadScreen(name="analyzer_load"))
        sm.add_widget(AnalyzerReviewScreen(name="analyzer_review"))

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

    def _refresh_ollama_screen(self) -> None:
        root = getattr(self, "root", None)
        if root is None:
            return

        try:
            screen = root.get_screen("ollama_config")
        except Exception:
            return

        if hasattr(screen, "refresh_ollama_status"):
            screen.refresh_ollama_status()
        if hasattr(screen, "refresh_local_models"):
            screen.refresh_local_models()

    def _run_in_thread(self, fn) -> None:
        threading.Thread(target=fn, daemon=True).start()

    def _start_ollama_in_background(self) -> None:
        def work():
            rc = ollama_service.start_service()

            def finish(*_args):
                if rc == 0:
                    self._refresh_ollama_screen()
                    return

                show_fading_alert(
                    "Start Ollama",
                    "BatLLM could not start Ollama. Open the Ollama screen for details.",
                    duration=2.5,
                    fade_duration=1.0,
                )

            Clock.schedule_once(finish, 0)

        self._run_in_thread(work)

    def _install_ollama_in_background(self) -> None:
        def work():
            rc, message = ollama_service.install_service()
            state = ollama_service.inspect_service_state()

            def finish(*_args):
                if rc == 0 and state.get("installed"):
                    if message:
                        show_fading_alert(
                            "Install Ollama",
                            message,
                            duration=2.5,
                            fade_duration=1.0,
                        )
                    self._refresh_ollama_screen()
                    self._handle_startup_ollama_state(state)
                    return

                show_fading_alert(
                    "Install Ollama",
                    message
                    or (
                        "Complete the Ollama installer, then return to BatLLM "
                        "and refresh the Ollama screen or restart the app."
                        if rc == 0
                        else "BatLLM could not launch the Ollama installer."
                    ),
                    duration=3.0,
                    fade_duration=1.0,
                )
                if rc == 0:
                    self._refresh_ollama_screen()

            Clock.schedule_once(finish, 0)

        self._run_in_thread(work)

    def _prompt_to_install_ollama(self) -> None:
        show_confirmation_dialog(
            "Install Ollama",
            "Ollama is not installed. Launch the official Ollama installer now?",
            self._install_ollama_in_background,
        )

    def _prompt_to_start_ollama(self, startup_model: str | None = None) -> None:
        startup_model = (startup_model or "").strip()
        model_suffix = f"\n\nBatLLM will warm: {startup_model}" if startup_model else ""
        show_confirmation_dialog(
            "Start Ollama",
            "Ollama is installed but not running. Start it now?" + model_suffix,
            self._start_ollama_in_background,
        )

    def _handle_startup_ollama_state(self, state: dict[str, object]) -> None:
        if not state.get("installed"):
            self._prompt_to_install_ollama()
            return

        if state.get("running"):
            return

        if config.get("ui", "auto_start_ollama"):
            self._start_ollama_in_background()
            return

        self._prompt_to_start_ollama(str(state.get("startup_model") or ""))

    def _run_startup_ollama_flow(self, *_args) -> None:
        if self._startup_ollama_flow_completed:
            return
        self._startup_ollama_flow_completed = True
        self._handle_startup_ollama_state(ollama_service.inspect_service_state())

    def on_start(self):
        Clock.schedule_once(self._run_startup_ollama_flow, 0)

    def on_stop(self):
        should_stop = bool(
            config.get("ui", "stop_ollama_on_exit")
            or config.get("ui", "auto_stop_ollama")
        )
        if not should_stop:
            return
        try:
            ollama_service.stop_service(verbose=False)
        except Exception:
            return

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
