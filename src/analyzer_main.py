"""Standalone BatLLM Game Analyzer application."""

from __future__ import annotations

import sys
from pathlib import Path

from kivy.config import Config
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivymd.app import MDApp

from configs.app_config import config
from game.session_schema import SessionFormatError, load_session_payload
from util.paths import asset_path, register_kivy_resource_paths, repo_path, view_path
from util.version import current_app_version
from view.analyzer_load_screen import AnalyzerLoadScreen
from view.analyzer_review_screen import AnalyzerReviewScreen


MIN_PYTHON = (3, 10)


def require_supported_python() -> None:
    """Exit early with a clear message on unsupported Python versions."""
    if sys.version_info >= MIN_PYTHON:
        return
    version = ".".join(str(part) for part in sys.version_info[:3])
    raise SystemExit(f"BatLLM Game Analyzer requires Python 3.10 or newer. Detected Python {version}.")


require_supported_python()
register_kivy_resource_paths()

Builder.load_file(str(view_path("analyzer_load_screen.kv")))
Builder.load_file(str(view_path("analyzer_review_screen.kv")))


class GameAnalyzerApp(MDApp):
    """Standalone analyzer entry point."""

    app_version = StringProperty(current_app_version())

    def __init__(self, initial_session: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.initial_session = initial_session

    def build(self):
        sm = ScreenManager(transition=SlideTransition(direction="left"))
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

        self.title = f"{config.get('ui', 'title')} Game Analyzer"
        return sm

    def on_start(self):
        if not self.initial_session:
            return
        load_screen = self.root.get_screen("analyzer_load")
        load_screen.load_preview(self.initial_session)
        try:
            payload = load_session_payload(Path(self.initial_session))
        except SessionFormatError as exc:
            load_screen.status_text = f"Compatibility: {exc}"
            return

        review = self.root.get_screen("analyzer_review")
        from analyzer_model import AnalyzerSessionModel

        review.load_session(AnalyzerSessionModel(payload, self.initial_session))
        self.root.current = "analyzer_review"


def main(argv: list[str] | None = None) -> int:
    require_supported_python()
    argv = argv or sys.argv[1:]
    initial_session = argv[0] if argv else None
    Config.set("kivy", "log_level", "error")
    Config.write()
    if hasattr(Window, "maximize"):
        Window.maximize()
    GameAnalyzerApp(initial_session=initial_session).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
