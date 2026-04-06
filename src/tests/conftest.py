from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

import pytest

from configs.app_config import CONFIG_PATH, config


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
def _restore_repo_config_state() -> None:
    original_text = CONFIG_PATH.read_text(encoding="utf-8")
    original_config = deepcopy(config.as_dict())
    original_path = getattr(config, "_path")

    yield

    setattr(config, "_config", deepcopy(original_config))
    setattr(config, "_path", original_path)
    CONFIG_PATH.write_text(original_text, encoding="utf-8")
