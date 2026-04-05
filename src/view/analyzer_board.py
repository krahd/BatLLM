"""Read-only board renderer used by the Game Analyzer."""

from __future__ import annotations

from typing import Any

from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.properties import DictProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.widget import Widget

from game.replay_engine import normalize_state_map
from view.normalized_canvas import NormalizedCanvas


class AnalyzerBoard(Widget):
    """Render a replay step without mutating game state."""

    state_by_bot = DictProperty({})
    rules_snapshot = DictProperty({})
    shot_path = ListProperty([])
    bot_filter = StringProperty("Both")
    highlight_bot_id = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pos=self._redraw,
            size=self._redraw,
            state_by_bot=self._redraw,
            rules_snapshot=self._redraw,
            shot_path=self._redraw,
            bot_filter=self._redraw,
            highlight_bot_id=self._redraw,
        )

    def set_replay_state(
        self,
        state_by_bot: dict[int, dict[str, Any]] | None,
        *,
        rules_snapshot: dict[str, Any] | None = None,
        shot_path: list[tuple[float, float]] | None = None,
        bot_filter: str = "Both",
        highlight_bot_id: int = 0,
    ) -> None:
        self.state_by_bot = normalize_state_map(state_by_bot)
        self.rules_snapshot = dict(rules_snapshot or {})
        self.shot_path = list(shot_path or [])
        self.bot_filter = bot_filter
        self.highlight_bot_id = int(highlight_bot_id or 0)

    def _redraw(self, *_args) -> None:
        self.render()

    def _bot_alpha(self, bot_id: int) -> float:
        if self.bot_filter == "Both":
            return 0.95
        if self.bot_filter == f"Bot {bot_id}":
            return 1.0
        return 0.28

    def render(self) -> None:
        self.canvas.clear()

        with NormalizedCanvas(self):
            Color(0.97, 0.97, 0.95, 1)
            Rectangle(pos=(0, 0), size=(1, 1))

            Color(0.12, 0.12, 0.15, 0.85)
            Line(rectangle=(0, 0, 1, 1), width=0.003)

            if self.shot_path:
                Color(0.82, 0.18, 0.18, 0.92)
                if len(self.shot_path) > 1:
                    points = [coord for point in self.shot_path for coord in point]
                    Line(points=points, width=0.004)
                x, y = self.shot_path[-1]
                Ellipse(pos=(x - 0.01, y - 0.01), size=(0.02, 0.02))

            shield_size = float(self.rules_snapshot.get("shield_size", 70.0) or 70.0)

            for bot_id in sorted(int(key) for key in self.state_by_bot):
                state = self.state_by_bot[bot_id]
                diameter = float(self.rules_snapshot.get("bot_diameter", 0.1) or 0.1)
                radius = diameter / 2
                alpha = self._bot_alpha(bot_id)
                fill = (0.56, 0.78, 1.0, alpha) if bot_id == 1 else (0.88, 0.60, 0.92, alpha)

                Color(*fill)
                Ellipse(pos=(state["x"] - radius, state["y"] - radius), size=(diameter, diameter))

                outline_width = 0.007 if bot_id == self.highlight_bot_id else 0.003
                Color(0.14, 0.14, 0.18, alpha)
                Line(
                    ellipse=(state["x"] - radius, state["y"] - radius, diameter, diameter),
                    width=outline_width,
                )

                if state.get("shield"):
                    Color(0.32, 0.30, 0.72, 0.95 if alpha > 0.5 else 0.45)
                    Line(
                        ellipse=(
                            state["x"] - radius,
                            state["y"] - radius,
                            diameter,
                            diameter,
                            90 - shield_size,
                            90 + shield_size,
                        ),
                        width=0.01,
                    )

                heading_len = radius * 0.95
                from math import cos, radians, sin

                rot = radians(float(state.get("rot", 0.0)))
                Color(0.14, 0.14, 0.18, alpha)
                Line(
                    points=(
                        state["x"],
                        state["y"],
                        state["x"] + cos(rot) * heading_len,
                        state["y"] + sin(rot) * heading_len,
                    ),
                    width=0.004,
                )
