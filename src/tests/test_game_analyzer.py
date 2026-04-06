from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

from analyzer_model import AnalyzerSessionModel
from game.session_schema import (
    SessionFormatError,
    UnsupportedLegacySession,
    build_session_payload,
    load_session_payload,
    validate_session_payload,
)
from util.version import current_app_version
from view.analyzer_load_screen import AnalyzerLoadScreen
from view.analyzer_review_screen import AnalyzerReviewScreen


def _sample_payload() -> dict:
    games = [
        {
            "game_id": 1,
            "start_time": "2026-04-04T10:00:00",
            "end_time": "2026-04-04T10:05:00",
            "winner": 1,
            "rounds": [
                {
                    "round": 1,
                    "start_time": "2026-04-04T10:00:00",
                    "end_time": "2026-04-04T10:01:00",
                    "gameplay_settings_snapshot": {
                        "bot_diameter": 0.1,
                        "bot_step_length": 0.03,
                        "bullet_damage": 5,
                        "bullet_diameter": 0.02,
                        "bullet_step_length": 0.01,
                        "shield_size": 70,
                        "shield_initial_state": True,
                        "initial_health": 30,
                        "turns_per_round": 2,
                        "total_rounds": 2,
                    },
                    "initial_state": {
                        "1": {"id": 1, "health": 30, "x": 0.2, "y": 0.5, "rot": 0, "shield": False},
                        "2": {"id": 2, "health": 30, "x": 0.4, "y": 0.5, "rot": 180, "shield": False},
                    },
                    "prompts": [
                        {"bot_id": 1, "prompt": "Reply with exactly B"},
                        {"bot_id": 2, "prompt": "Reply with exactly S1"},
                    ],
                    "turns": [
                        {
                            "turn": 1,
                            "start_time": "2026-04-04T10:00:01",
                            "end_time": "2026-04-04T10:00:05",
                            "pre_state": {
                                "1": {"id": 1, "health": 30, "x": 0.2, "y": 0.5, "rot": 0, "shield": False},
                                "2": {"id": 2, "health": 30, "x": 0.4, "y": 0.5, "rot": 180, "shield": False},
                            },
                            "post_state": {
                                "1": {"id": 1, "health": 30, "x": 0.2, "y": 0.5, "rot": 0, "shield": False},
                                "2": {"id": 2, "health": 25, "x": 0.4, "y": 0.5, "rot": 180, "shield": True},
                            },
                            "plays": [
                                {"bot_id": 1, "llm_response": "B", "cmd": "B"},
                                {"bot_id": 2, "llm_response": "S1", "cmd": "S1"},
                            ],
                        }
                    ],
                }
            ],
        }
    ]
    return build_session_payload(
        games=deepcopy(games),
        app_version=current_app_version(),
        saved_at="2026-04-04T10:06:00",
    )


def _load_module(module_name: str, monkeypatch):
    fake_window = SimpleNamespace(
        size=(1280, 720),
        bind=lambda *args, **kwargs: None,
        unbind=lambda *args, **kwargs: None,
        maximize=lambda *args, **kwargs: None,
    )
    monkeypatch.setattr("kivy.lang.Builder.load_file", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("util.paths.register_kivy_resource_paths", lambda: None)
    monkeypatch.setattr("kivy.core.window.Window", fake_window, raising=False)
    monkeypatch.setattr("kivymd.theming.Window", fake_window, raising=False)
    if module_name in sys.modules:
        return importlib.reload(sys.modules[module_name])
    return importlib.import_module(module_name)


class _FakeScreenManager:
    def __init__(self, *args, **kwargs):
        self.transition = kwargs.get("transition")
        self._screens = {}

    def add_widget(self, widget) -> None:
        self._screens[widget.name] = widget

    def has_screen(self, name: str) -> bool:
        return name in self._screens


class _FakeScreen:
    def __init__(self, name: str):
        self.name = name
        self.on_request_close = lambda *args, **kwargs: True


def test_validate_session_payload_rejects_legacy_list() -> None:
    legacy = [{"game_id": 1, "rounds": []}]

    try:
        validate_session_payload(legacy)
    except UnsupportedLegacySession as exc:
        assert "legacy BatLLM format" in str(exc)
    else:
        raise AssertionError("Legacy list payload should be rejected")


def test_load_session_payload_reports_invalid_json(tmp_path: Path) -> None:
    broken = tmp_path / "broken.json"
    broken.write_text("{not-json", encoding="utf-8")

    try:
        load_session_payload(broken)
    except SessionFormatError as exc:
        assert "Invalid JSON" in str(exc)
    else:
        raise AssertionError("Broken JSON should raise SessionFormatError")


def test_analyzer_model_replays_turns_and_preserves_selection_state() -> None:
    model = AnalyzerSessionModel(_sample_payload(), "session.json")
    model.set_game_index(0)
    model.set_round_index(0)
    model.set_flat_index(1)

    rows = model.session_tree_rows()

    assert model.game_index == 0
    assert model.round_index == 0
    assert model.flat_index == 1
    assert any(row.kind == "turn" and "damage" in row.badge_tokens for row in rows)
    assert "bullet_diameter" in model.format_round_settings()
    assert "bullet_damage" in model.format_round_settings()
    assert "Bot 2 took 5 damage" in model.format_insights()
    assert model.current_turn_replay() is not None
    assert model.current_turn_replay().mismatch is False


def test_analyzer_load_screen_opens_valid_session(tmp_path: Path) -> None:
    payload = _sample_payload()
    session_path = tmp_path / "session.json"
    session_path.write_text(json.dumps(payload), encoding="utf-8")

    review_screen = SimpleNamespace(model=None)
    review_screen.load_session = lambda model: setattr(review_screen, "model", model)

    manager = SimpleNamespace(
        current="analyzer_load",
        get_screen=lambda name: review_screen if name == "analyzer_review" else None,
    )
    load_screen = SimpleNamespace(
        selected_path=str(session_path),
        status_text="",
        manager=manager,
    )

    AnalyzerLoadScreen.open_selected_session(load_screen)

    assert manager.current == "analyzer_review"
    assert review_screen.model is not None
    assert review_screen.model.source_name == "session.json"


def test_analyzer_load_screen_escape_goes_back(monkeypatch) -> None:
    screen = AnalyzerLoadScreen()
    go_back_called = {"value": False}

    monkeypatch.setattr(
        screen,
        "go_back",
        lambda: go_back_called.__setitem__("value", True),
    )

    assert screen.handle_window_key_down(None, 27) is True
    assert go_back_called["value"] is True


def test_analyzer_review_screen_escape_goes_back(monkeypatch) -> None:
    screen = AnalyzerReviewScreen()
    go_back_called = {"value": False}

    monkeypatch.setattr(
        screen,
        "go_back",
        lambda: go_back_called.__setitem__("value", True),
    )

    assert screen.handle_window_key_down(None, 27) is True
    assert go_back_called["value"] is True


def test_main_app_build_includes_analyzer_screens(monkeypatch) -> None:
    main_module = _load_module("main", monkeypatch)
    monkeypatch.setattr(main_module, "ScreenManager", _FakeScreenManager)
    monkeypatch.setattr(main_module, "HomeScreen", _FakeScreen)
    monkeypatch.setattr(main_module, "SettingsScreen", _FakeScreen)
    monkeypatch.setattr(main_module, "HistoryScreen", _FakeScreen)
    monkeypatch.setattr(main_module, "OllamaConfigScreen", _FakeScreen)
    monkeypatch.setattr(main_module, "AnalyzerLoadScreen", _FakeScreen)
    monkeypatch.setattr(main_module, "AnalyzerReviewScreen", _FakeScreen)
    app = main_module.BatLLM()

    root = app.build()

    assert root.has_screen("analyzer_load")
    assert root.has_screen("analyzer_review")


def test_standalone_analyzer_builds_without_ollama(monkeypatch) -> None:
    analyzer_module = _load_module("analyzer_main", monkeypatch)
    monkeypatch.setattr(analyzer_module, "ScreenManager", _FakeScreenManager)
    monkeypatch.setattr(analyzer_module, "AnalyzerLoadScreen", _FakeScreen)
    monkeypatch.setattr(analyzer_module, "AnalyzerReviewScreen", _FakeScreen)
    app = analyzer_module.GameAnalyzerApp()

    root = app.build()

    assert root.has_screen("analyzer_load")
    assert root.has_screen("analyzer_review")


def test_analyzer_kv_files_load_with_registered_widgets() -> None:
    root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env["KIVY_NO_FILELOG"] = "1"
    env["KIVY_NO_ARGS"] = "1"

    script = """
import sys
sys.path.insert(0, "src")
from kivy.lang import Builder
import view.analyzer_load_screen
import view.analyzer_review_screen
Builder.load_file("src/view/analyzer_load_screen.kv")
Builder.load_file("src/view/analyzer_review_screen.kv")
print("kv-ok")
"""

    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "kv-ok" in proc.stdout
