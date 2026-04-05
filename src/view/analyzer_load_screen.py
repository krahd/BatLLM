"""Load screen for the BatLLM Game Analyzer."""

from __future__ import annotations

from pathlib import Path

from kivy.app import App
from kivy.properties import ListProperty, StringProperty
from kivy.uix.screenmanager import Screen

from analyzer_model import AnalyzerSessionModel
from configs.app_config import config
from game.session_schema import SessionFormatError, load_session_payload, summarize_session_payload
from util.paths import resolve_saved_sessions_dir
from util.utils import switch_screen
from view import analyzer_theme


class AnalyzerLoadScreen(Screen):
    """Open and validate saved BatLLM sessions for replay."""

    selected_path = StringProperty("")
    summary_text = StringProperty("Choose a saved session JSON to inspect.")
    status_text = StringProperty("Awaiting selection.")
    status_color = ListProperty(list(analyzer_theme.TEXT_SECONDARY))
    recent_sessions_text = StringProperty("No saved sessions found yet.")

    def on_pre_enter(self, *_args) -> None:
        saved_dir = self.default_saved_sessions_dir()
        if "filechooser" in self.ids:
            self.ids.filechooser.path = str(saved_dir)
        self.refresh_recent_sessions()

    def default_saved_sessions_dir(self) -> Path:
        folder_name = config.get("data", "saved_sessions_folder") or "saved_sessions"
        return resolve_saved_sessions_dir(folder_name)

    def refresh_recent_sessions(self) -> None:
        saved_dir = self.default_saved_sessions_dir()
        sessions = sorted(saved_dir.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
        self._populate_recent_buttons(sessions[:12])
        if sessions:
            lines = [f"{index + 1}. {path.name}" for index, path in enumerate(sessions[:6])]
            self.recent_sessions_text = "\n".join(lines)
        else:
            self.recent_sessions_text = "No saved sessions found yet."

    def _populate_recent_buttons(self, paths: list[Path]) -> None:
        container = self.ids.get("recent_sessions_box")
        if container is None:
            return
        container.clear_widgets()

        from kivy.metrics import dp
        from kivy.uix.button import Button
        from kivy.uix.label import Label

        if not paths:
            empty_label = Label(
                text="No analyzer-compatible saves have been exported yet.",
                size_hint_y=None,
                height=dp(54),
                halign="left",
                valign="middle",
                **analyzer_theme.label_kwargs(muted=True),
            )
            empty_label.bind(
                width=lambda inst, _value: setattr(inst, "text_size", (inst.width, None))
            )
            container.add_widget(empty_label)
            return

        for path in paths:
            button = Button(
                text=path.name,
                size_hint_y=None,
                height=dp(42),
                halign="left",
                valign="middle",
                **analyzer_theme.button_kwargs("neutral"),
            )
            button.text_size = (button.width - dp(20), None)
            button.shorten = True
            button.shorten_from = "right"
            button.bind(width=lambda inst, _value: setattr(inst, "text_size", (inst.width - dp(20), None)))
            button.bind(on_release=lambda _button, value=path: self.open_recent_session(value))
            container.add_widget(button)

    def open_recent_session(self, path: Path) -> None:
        if "filechooser" in self.ids:
            self.ids.filechooser.path = str(path.parent)
            self.ids.filechooser.selection = [str(path)]
        self.load_preview(path)

    def on_file_selection(self, selection: list[str]) -> None:
        if not selection:
            self.selected_path = ""
            self.status_text = "Awaiting selection."
            self.status_color = list(analyzer_theme.TEXT_SECONDARY)
            self.summary_text = "Choose a saved session JSON to inspect."
            return
        self.load_preview(selection[0])

    def load_preview(self, path_like: str | Path) -> None:
        path = Path(path_like)
        self.selected_path = str(path)
        if path.is_dir():
            self.status_text = "Select a JSON session file, not a folder."
            self.status_color = list(analyzer_theme.ERROR_TEXT_DARK)
            self.summary_text = ""
            return

        try:
            payload = load_session_payload(path)
        except SessionFormatError as exc:
            self.status_text = f"Compatibility: {exc}"
            self.status_color = list(analyzer_theme.ERROR_TEXT_DARK)
            self.summary_text = f"File: {path.name}\nStatus: incompatible"
            return

        summary = summarize_session_payload(payload)
        self.status_text = "Compatibility: analyzer-compatible"
        self.status_color = list(analyzer_theme.SUCCESS_TEXT)
        self.summary_text = (
            f"File: {path.name}\n"
            f"Schema: v{summary['schema_version']}\n"
            f"Saved: {summary.get('saved_at') or 'unknown'}\n"
            f"App: {summary.get('app_version') or 'unknown'}\n"
            f"Games: {summary['game_count']}\n"
            f"Rounds: {summary['round_count']}\n"
            f"Turns: {summary['turn_count']}\n"
            f"Status: Analyzer-compatible"
        )

    def open_selected_session(self) -> None:
        path_text = self.selected_path.strip()
        if not path_text:
            self.status_text = "Select a JSON session before opening the analyzer."
            self.status_color = list(analyzer_theme.ERROR_TEXT_DARK)
            return

        path = Path(path_text)
        try:
            payload = load_session_payload(path)
        except SessionFormatError as exc:
            self.status_text = f"Compatibility: {exc}"
            self.status_color = list(analyzer_theme.ERROR_TEXT_DARK)
            return

        review = self.manager.get_screen("analyzer_review")
        review.load_session(AnalyzerSessionModel(payload, path))
        switch_screen(self.manager, "analyzer_review", direction="left")

    def go_back(self) -> None:
        if self.manager is not None and self.manager.has_screen("home"):
            switch_screen(self.manager, "home", direction="right")
            return
        app = App.get_running_app()
        if app is not None:
            app.stop()
