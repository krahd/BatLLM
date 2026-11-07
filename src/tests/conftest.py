from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace

import pytest

# Configuration is loaded during test-module imports, before fixtures run.
_TEST_HOME = Path(tempfile.mkdtemp(prefix="batllm-pytest-"))
os.environ["BATLLM_HOME"] = str(_TEST_HOME)

from configs.app_config import config


@pytest.fixture(autouse=True)
def _isolate_test_proxies(monkeypatch) -> None:
    """Keep test-owned HTTP endpoints independent of the host's proxy setup."""
    for key in ("http_proxy", "https_proxy", "all_proxy", "no_proxy"):
        monkeypatch.delenv(key, raising=False)
        monkeypatch.delenv(key.upper(), raising=False)
    # Modelito caches urllib's proxy configuration when first imported.
    monkeypatch.setattr("modelito._http_deadline._PROXIES", {})


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
    original_config = deepcopy(config._config)
    original_overrides = deepcopy(config._overrides)
    config._overrides = {}
    original_path = getattr(config, "_path")
    setattr(config, "_path", tmp_path / "config.yaml")

    yield

    setattr(config, "_config", deepcopy(original_config))
    setattr(config, "_path", original_path)
    config._overrides = original_overrides
