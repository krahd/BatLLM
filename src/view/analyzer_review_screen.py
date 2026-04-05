"""Review screen for the BatLLM Game Analyzer."""

from __future__ import annotations

from pathlib import Path

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import NumericProperty, ObjectProperty, StringProperty
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from analyzer_model import AnalyzerSessionModel, AnalyzerTreeRow
from game.session_schema import SessionFormatError, load_session_payload
from util.utils import switch_screen
from view.analyzer_board import AnalyzerBoard  # Register custom widget before KV loads.
from view import analyzer_theme


class AnalyzerReviewScreen(Screen):
    """Read-only session replay surface."""

    current_file = StringProperty("")
    session_title = StringProperty("Game Analyzer")
    timeline_caption = StringProperty("No replay loaded.")
    event_ribbon_text = StringProperty("Open a saved session to begin.")
    model = ObjectProperty(allownone=True)
    playback_rate = NumericProperty(1.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._playback_event = None
        self._updating_slider = False
        self._active_tree_filters: set[str] = set()

    def on_leave(self, *_args) -> None:
        self.stop_playback()

    def load_session(self, model: AnalyzerSessionModel) -> None:
        self.stop_playback()
        self.model = model
        self.current_file = model.source_name
        self.session_title = f"Game Analyzer | {model.source_name}"
        self._active_tree_filters.clear()
        self._sync_filter_buttons()
        self._refresh_view()

    def reload_current_session(self) -> None:
        model = self.model
        if model is None:
            return
        try:
            payload = load_session_payload(model.source_path)
        except SessionFormatError as exc:
            self.event_ribbon_text = f"Reload failed: {exc}"
            return
        self.load_session(AnalyzerSessionModel(payload, model.source_path))

    def open_load_screen(self) -> None:
        self.stop_playback()
        switch_screen(self.manager, "analyzer_load", direction="right")

    def go_back(self) -> None:
        self.open_load_screen()

    def on_game_selected(self, label: str) -> None:
        if self.model is None or label not in self.model.game_labels():
            return
        self.stop_playback()
        self.model.set_game_index(self.model.game_labels().index(label))
        self._refresh_view()

    def on_round_selected(self, label: str) -> None:
        if self.model is None or label not in self.model.round_labels():
            return
        self.stop_playback()
        self.model.set_round_index(self.model.round_labels().index(label))
        self._refresh_view()

    def on_bot_filter_selected(self, label: str) -> None:
        if self.model is None:
            return
        self.model.set_bot_filter(label)
        self._refresh_view(skip_tree=True)

    def set_tree_filter(self, token: str, enabled: bool) -> None:
        if enabled:
            self._active_tree_filters.add(token)
        else:
            self._active_tree_filters.discard(token)
        self._refresh_tree()

    def previous_step(self) -> None:
        if self.model is None:
            return
        self.stop_playback()
        self.model.set_flat_index(self.model.flat_index - 1)
        self._refresh_view(skip_tree=True)

    def next_step(self) -> None:
        if self.model is None:
            return
        self.stop_playback()
        self.model.set_flat_index(self.model.flat_index + 1)
        self._refresh_view(skip_tree=True)

    def first_step(self) -> None:
        if self.model is None:
            return
        self.stop_playback()
        self.model.set_flat_index(0)
        self._refresh_view(skip_tree=True)

    def last_step(self) -> None:
        if self.model is None:
            return
        self.stop_playback()
        self.model.set_flat_index(max(0, self.model.step_count() - 1))
        self._refresh_view(skip_tree=True)

    def on_timeline_value(self, value: float) -> None:
        if self.model is None or self._updating_slider:
            return
        self.stop_playback()
        self.model.set_flat_index(int(value))
        self._refresh_view(skip_tree=True)

    def set_playback_rate(self, label: str) -> None:
        mapping = {"0.5x": 0.5, "1x": 1.0, "2x": 2.0}
        self.playback_rate = mapping.get(label, 1.0)
        if self._playback_event is not None:
            self.stop_playback()
            self.start_playback()

    def toggle_playback(self) -> None:
        if self._playback_event is not None:
            self.stop_playback()
            return
        self.start_playback()

    def start_playback(self) -> None:
        if self.model is None or self.model.step_count() <= 1:
            return
        if self.model.flat_index >= self.model.step_count() - 1:
            self.model.set_flat_index(0)
        interval = max(0.2, 0.8 / max(0.5, self.playback_rate))
        self._playback_event = Clock.schedule_interval(self._advance_playback, interval)
        self._update_playback_button()

    def stop_playback(self) -> None:
        if self._playback_event is not None:
            self._playback_event.cancel()
            self._playback_event = None
        self._update_playback_button()

    def _advance_playback(self, _dt: float) -> bool:
        if self.model is None:
            self.stop_playback()
            return False
        if self.model.flat_index >= self.model.step_count() - 1:
            self.stop_playback()
            return False
        self.model.set_flat_index(self.model.flat_index + 1)
        self._refresh_view(skip_tree=True)
        return True

    def jump_to_tree_row(self, row: AnalyzerTreeRow) -> None:
        if self.model is None:
            return
        self.stop_playback()
        if row.game_index is not None:
            self.model.set_game_index(row.game_index)
        if row.round_index is not None:
            self.model.set_round_index(row.round_index)
        if row.flat_index is not None:
            self.model.set_flat_index(row.flat_index)
        self._refresh_view()

    def _refresh_view(self, *, skip_tree: bool = False) -> None:
        model = self.model
        if model is None or not self.ids:
            return

        self.current_file = model.source_name
        self.session_title = f"Game Analyzer | {model.source_name}"

        game_spinner = self.ids.game_spinner
        game_spinner.values = model.game_labels()
        if game_spinner.values:
            game_spinner.text = game_spinner.values[model.game_index]

        round_spinner = self.ids.round_spinner
        round_spinner.values = model.round_labels()
        if round_spinner.values:
            round_spinner.text = round_spinner.values[model.round_index]

        bot_spinner = self.ids.bot_filter_spinner
        bot_spinner.values = model.bot_filter_labels()
        bot_spinner.text = model.bot_filter

        self.ids.file_name_label.text = model.source_name
        self.ids.prompts_text.text = model.format_prompts()
        self.ids.plays_text.text = model.format_plays()
        self.ids.state_diff_text.text = model.format_state_diff()
        self.ids.round_settings_text.text = model.format_round_settings()
        self.ids.insights_text.text = model.format_insights()

        self.timeline_caption = model.timeline_label()
        self.ids.timeline_summary.text = self.timeline_caption

        entry = model.current_entry()
        play = entry.get("play") or {}
        active_bot_id = int(play.get("bot_id", 0) or 0)
        board = self.ids.analyzer_board
        board.set_replay_state(
            entry.get("state_by_bot", {}),
            rules_snapshot=model.current_round_settings(),
            shot_path=entry.get("shot_path", []),
            bot_filter=model.bot_filter,
            highlight_bot_id=active_bot_id,
        )

        self._refresh_hud()
        self._refresh_event_ribbon()
        self._refresh_slider()
        if not skip_tree:
            self._refresh_tree()
        self._update_playback_button()

    def _refresh_slider(self) -> None:
        if self.model is None:
            return
        slider = self.ids.timeline_slider
        self._updating_slider = True
        slider.min = 0
        slider.max = max(0, self.model.step_count() - 1)
        slider.step = 1
        slider.value = self.model.flat_index
        self._updating_slider = False

    def _refresh_hud(self) -> None:
        if self.model is None:
            return
        entry = self.model.current_entry()
        states = entry.get("state_by_bot", {})
        for bot_id in (1, 2):
            label = self.ids[f"bot_{bot_id}_hud"]
            state = states.get(bot_id, {})
            if not state:
                label.text = f"[b]Bot {bot_id}[/b]\nNo state"
                continue
            label.text = (
                f"[b]Bot {bot_id}[/b]\n"
                f"x={state.get('x', 0.0):.3f}\n"
                f"y={state.get('y', 0.0):.3f}\n"
                f"rot={state.get('rot', 0.0):.1f}d\n"
                f"shield={'ON' if state.get('shield') else 'OFF'}\n"
                f"health={state.get('health', 0)}"
            )

    def _refresh_event_ribbon(self) -> None:
        if self.model is None:
            return
        entry = self.model.current_entry()
        events = entry.get("events", [])
        labels = [event.label for event in events] or ["Turn start"]
        self.event_ribbon_text = " | ".join(labels)
        self.ids.event_ribbon.text = self.event_ribbon_text

    def _tree_rows_to_render(self) -> list[AnalyzerTreeRow]:
        if self.model is None:
            return []
        rows = self.model.session_tree_rows()
        if not self._active_tree_filters:
            return rows
        rendered: list[AnalyzerTreeRow] = []
        for row in rows:
            if row.kind != "turn":
                rendered.append(row)
                continue
            if set(row.badge_tokens) & self._active_tree_filters:
                rendered.append(row)
        return rendered

    def _refresh_tree(self) -> None:
        if self.model is None:
            return
        container = self.ids.tree_container
        container.clear_widgets()
        rows = self._tree_rows_to_render()

        for row in rows:
            if row.kind == "header":
                widget = Label(
                    text=f"[b]{row.label}[/b]",
                    markup=True,
                    size_hint_y=None,
                    height=dp(32),
                    halign="left",
                    valign="middle",
                    **analyzer_theme.label_kwargs(),
                )
                widget.bind(width=lambda inst, _value: setattr(inst, "text_size", (inst.width, None)))
                container.add_widget(widget)
                continue

            is_selected = (
                row.flat_index is not None
                and row.game_index == self.model.game_index
                and row.round_index == self.model.round_index
                and row.flat_index == self.model.flat_index
            )
            button = Button(
                text=row.label if not row.badge_text else f"{row.label} {row.badge_text}",
                size_hint_y=None,
                height=dp(38 if row.kind == "subheader" else 36),
                halign="left",
                valign="middle",
                **analyzer_theme.tree_button_kwargs(
                    row.kind,
                    selected=is_selected,
                    badge_tokens=row.badge_tokens,
                ),
            )
            button.bind(size=lambda inst, _value: setattr(inst, "text_size", (inst.width - dp(16), None)))
            button.bind(on_release=lambda _button, current_row=row: self.jump_to_tree_row(current_row))
            container.add_widget(button)

    def _sync_filter_buttons(self) -> None:
        for token, widget_id in (
            ("errors", "errors_filter"),
            ("damage", "damage_filter"),
            ("shield", "shield_filter"),
            ("mismatch", "mismatch_filter"),
        ):
            widget = self.ids.get(widget_id)
            if widget is not None:
                widget.state = "down" if token in self._active_tree_filters else "normal"

    def _update_playback_button(self) -> None:
        button = self.ids.get("play_pause_button")
        if button is not None:
            button.text = "Pause" if self._playback_event is not None else "Play"
