"""Configuration persistence contracts; all writable paths are temporary."""
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from configs.app_config import AppConfig, SHIPPED_CONFIG_PATH
from llm import service
from util import paths
from view import ollama_config_screen as screen_module


@pytest.fixture
def runtime_home(monkeypatch, tmp_path):
    """Redirect both explicit and implicit configuration homes away from user state."""
    home = tmp_path / "preferences"
    monkeypatch.setenv("BATLLM_HOME", str(home))
    monkeypatch.setattr(paths, "default_batllm_home", lambda: home)
    return home


@pytest.mark.parametrize("explicit", [False, True])
def test_first_launch_save_reload_preserves_shipped_file(monkeypatch, runtime_home, explicit):
    if not explicit:
        monkeypatch.delenv("BATLLM_HOME")
    original = SHIPPED_CONFIG_PATH.read_bytes()
    preferences = AppConfig()
    assert preferences.get("llm", "model") == "smollm2"
    assert preferences.get("llm", "last_served_model") == ""
    assert not (runtime_home / "config.yaml").exists()
    preferences.set("llm", "model", "qwen3:8b")
    preferences.set("ui", "confirm_on_exit", False)
    preferences.save()
    reloaded = AppConfig()
    assert reloaded.get("llm", "model") == "qwen3:8b"
    assert reloaded.get("ui", "confirm_on_exit") is False
    assert (runtime_home / "config.yaml").is_file()
    assert SHIPPED_CONFIG_PATH.read_bytes() == original


def test_explicit_home_overrides_platform_home(monkeypatch, runtime_home, tmp_path):
    other = tmp_path / "other"
    monkeypatch.setattr(paths, "default_batllm_home", lambda: other)
    AppConfig().save()
    assert (runtime_home / "config.yaml").is_file()
    assert not other.exists()


def test_legacy_checkout_preferences_are_preserved(runtime_home, tmp_path):
    shipped = tmp_path / "legacy-checkout.yaml"
    shipped.write_text("llm:\n  model: old-model:latest\n  port: 12345\nui:\n  font_size: 22\n", encoding="utf-8")
    original = shipped.read_bytes()
    preferences = AppConfig(default_path=shipped)
    preferences.save()
    assert shipped.read_bytes() == original
    # Simulate upgrading the shipped defaults after preferences have been saved.
    shipped.write_text("llm:\n  model: smollm2\n  port: 11434\n", encoding="utf-8")
    reloaded = AppConfig(default_path=shipped)
    assert reloaded.get("llm", "model") == "old-model:latest"
    assert reloaded.get("llm", "port") == 12345
    assert reloaded.get("ui", "font_size") == 22
    assert (runtime_home / "config.yaml").read_bytes() != original


def test_existing_user_overlay_wins_and_unknown_settings_survive(runtime_home):
    runtime_home.mkdir()
    saved = runtime_home / "config.yaml"
    saved.write_text("llm:\n  model: existing:latest\n  model_timeouts:\n    existing:latest: 150\ncustom:\n  keep: value\n", encoding="utf-8")
    preferences = AppConfig()
    assert preferences.get("llm", "model") == "existing:latest"
    preferences.set("ui", "font_size", 24)
    preferences.save()
    reloaded = AppConfig()
    assert reloaded.get("custom", "keep") == "value"
    assert reloaded.get("llm", "model_timeouts") == {"existing:latest": 150}
    assert reloaded.get("ui", "font_size") == 24


@pytest.mark.parametrize("via_service", [False, True])
def test_explicit_write_to_shipped_defaults_is_rejected(tmp_path, via_service):
    shipped = tmp_path / "defaults.yaml"
    shipped.write_text("llm:\n  model: smollm2\n", encoding="utf-8")
    original = shipped.read_bytes()
    if via_service:
        # The actual shipped path must also be guarded by the service writer.
        with pytest.raises(ValueError, match="shipped"):
            service.save_last_served_model("qwen3:8b", SHIPPED_CONFIG_PATH)
    else:
        preferences = AppConfig(path=shipped, default_path=shipped)
        with pytest.raises(ValueError, match="shipped"):
            preferences.save()
        with pytest.raises(ValueError, match="shipped"):
            AppConfig(path=tmp_path / "user.yaml").save(SHIPPED_CONFIG_PATH)
    assert shipped.read_bytes() == original


def test_service_save_preserves_preferences_and_defaults(runtime_home):
    original = SHIPPED_CONFIG_PATH.read_bytes()
    preferences = AppConfig()
    preferences.set("llm", "model", "qwen3:8b")
    preferences.save()
    service.save_last_served_model(" qwen3:8b ")
    reloaded = AppConfig()
    assert reloaded.get("llm", "last_served_model") == "qwen3:8b"
    assert reloaded.get("llm", "model") == "qwen3:8b"
    assert service.load_config_data()["llm"]["model"] == "qwen3:8b"
    assert SHIPPED_CONFIG_PATH.read_bytes() == original


def test_model_table_row_selection_persists_only_name(monkeypatch, runtime_home):
    preferences = AppConfig()
    monkeypatch.setattr(screen_module, "config", preferences)
    screen = SimpleNamespace(
        selected_local_model="qwen3:8b   abc123   5 GB   2 months ago",
        _set_status=lambda _text: None,
        _append_log=lambda _text: None,
        # Readiness has not completed: selection must not be persisted.
        _run_in_thread=lambda _work: None,
    )
    screen_module.OllamaConfigScreen.set_model_from_selection(screen)
    assert AppConfig().get("llm", "model") == "smollm2"
    assert not (runtime_home / "config.yaml").exists()



@pytest.mark.parametrize(
    ("platform", "os_name", "appdata", "relative"),
    [
        ("darwin", "posix", "", "Library/Application Support/BatLLM"),
        ("linux", "posix", "", ".local/share/BatLLM"),
        ("win32", "nt", "", "AppData/Roaming/BatLLM"),
        ("win32", "nt", "roaming", "roaming/BatLLM"),
    ],
)
def test_platform_default_config_paths(monkeypatch, tmp_path, platform, os_name, appdata, relative):
    monkeypatch.setattr(Path, "home", classmethod(lambda _cls: tmp_path))
    monkeypatch.setattr(paths, "sys", SimpleNamespace(platform=platform))
    environment = {"APPDATA": str(tmp_path / appdata)} if appdata else {}
    monkeypatch.setattr(paths, "os", SimpleNamespace(name=os_name, environ=environment))
    assert paths.resolve_config_path() == tmp_path / relative / "config.yaml"


def test_failed_atomic_save_preserves_existing_preferences(monkeypatch, runtime_home):
    preferences = AppConfig()
    preferences.save()
    saved = runtime_home / "config.yaml"
    original = saved.read_bytes()
    preferences.set("llm", "model", "qwen3:8b")

    def fail_replace(*_args):
        raise OSError("simulated replacement failure")

    monkeypatch.setattr("configs.app_config.os.replace", fail_replace)
    with pytest.raises(OSError, match="simulated"):
        preferences.save()
    assert saved.read_bytes() == original
    assert not list(runtime_home.glob(".batllm-*.tmp"))


def test_standalone_editor_uses_user_preferences(monkeypatch, runtime_home):
    from importlib import import_module

    # The editor sets minimum window dimensions at import time.
    monkeypatch.setattr("kivy.core.window.Window", SimpleNamespace())
    editor = import_module("configs.configurator")
    original = SHIPPED_CONFIG_PATH.read_bytes()
    target = editor.BatLLMConfigApp._default_config_path(None)
    assert target == str(runtime_home / "config.yaml")
    manager = editor.ConfigManager(target)
    data = manager.load()
    assert data["llm"]["model"] == "smollm2"
    data["llm"]["model"] = "qwen3:8b"
    manager.save(data)
    assert AppConfig().get("llm", "model") == "qwen3:8b"
    with pytest.raises(ValueError, match="shipped"):
        editor.ConfigManager(str(SHIPPED_CONFIG_PATH))
    assert SHIPPED_CONFIG_PATH.read_bytes() == original
