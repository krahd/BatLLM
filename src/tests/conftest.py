from __future__ import annotations

from types import SimpleNamespace

import pytest


@pytest.fixture(autouse=True)
def _disable_kivy_window_requirement(monkeypatch) -> None:
    monkeypatch.setattr("kivy.base.EventLoop.ensure_window", lambda *args, **kwargs: None)
    monkeypatch.setattr("kivy.base.EventLoop.window", SimpleNamespace(dpi=96), raising=False)
    monkeypatch.setattr(
        "util.utils.Window",
        SimpleNamespace(request_keyboard=lambda *args, **kwargs: None),
        raising=False,
    )
    monkeypatch.setattr("view.ollama_config_screen.show_fading_alert", lambda *args, **kwargs: None)
    monkeypatch.setattr("view.ollama_config_screen.show_confirmation_dialog", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "view.ollama_config_screen.show_text_input_dialog",
        lambda *args, **kwargs: None,
        raising=False,
    )
