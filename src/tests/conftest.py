from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

import pytest

from configs.app_config import config


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
    monkeypatch.setattr("view.ollama_config_screen.show_confirmation_dialog",
                        lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "view.ollama_config_screen.show_text_input_dialog",
        lambda *args, **kwargs: None,
        raising=False,
    )


@pytest.fixture(autouse=True)
def _isolate_config_state(tmp_path) -> None:
    """Keep configuration writes inside the per-test temporary directory."""
    original_config = deepcopy(config.as_dict())
    original_path = getattr(config, "_path")
    setattr(config, "_path", tmp_path / "config.yaml")

    yield

    setattr(config, "_config", deepcopy(original_config))
    setattr(config, "_path", original_path)
