from __future__ import annotations

from typing import Callable

from view.ollama_config_screen import OllamaConfigScreen
from view.settings_screen import SettingsScreen


class DummyProc:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class DummyManager:
    def __init__(self, current: str = "settings"):
        self.current = current


def _run_sync(screen: OllamaConfigScreen):
    screen._run_in_thread = lambda fn: fn()  # type: ignore[method-assign]


def test_settings_navigates_to_ollama_screen() -> None:
    screen = SettingsScreen()
    screen.manager = DummyManager(current="settings")

    screen.go_to_ollama_config_screen()

    assert screen.manager.current == "ollama_config"


def test_ollama_screen_navigates_back_to_settings() -> None:
    screen = OllamaConfigScreen()
    screen.manager = DummyManager(current="ollama_config")

    screen.go_to_settings_screen()

    assert screen.manager.current == "settings"


def test_start_and_stop_call_scripts() -> None:
    screen = OllamaConfigScreen()
    calls = []
    _run_sync(screen)

    def fake_run_script(script_name: str, *args: str):
        calls.append((script_name, args))
        return DummyProc(returncode=0, stdout="ok", stderr="")

    screen._run_script = fake_run_script  # type: ignore[method-assign]
    screen.refresh_local_models = lambda: None  # type: ignore[method-assign]

    screen.start_ollama()
    screen.stop_ollama()

    assert ("start_ollama.sh", ()) in calls
    assert ("stop_ollama.sh", ("-v",)) in calls


def test_start_failure_prompts_install_guidance() -> None:
    screen = OllamaConfigScreen()
    _run_sync(screen)
    prompted = {"value": False}
    original_schedule = screen._set_status.__globals__["Clock"].schedule_once

    def run_now(callback, _dt=0):
        callback(0)

    screen._set_status.__globals__["Clock"].schedule_once = run_now

    screen._run_script = lambda *_args, **_kwargs: DummyProc(  # type: ignore[method-assign]
        returncode=1,
        stdout="",
        stderr="ollama: command not found",
    )
    screen._open_install_guidance = lambda: prompted.__setitem__(
        "value", True)  # type: ignore[method-assign]

    try:
        screen.start_ollama()
        assert prompted["value"] is True
    finally:
        screen._set_status.__globals__["Clock"].schedule_once = original_schedule


def test_set_model_from_selection_persists(monkeypatch) -> None:
    screen = OllamaConfigScreen()
    saved = {"set": None, "saved": False}

    def fake_set(section: str, key: str, value: str):
        saved["set"] = (section, key, value)

    def fake_save():
        saved["saved"] = True

    monkeypatch.setattr("view.ollama_config_screen.config.set", fake_set)
    monkeypatch.setattr("view.ollama_config_screen.config.save", fake_save)

    screen.selected_local_model = "mistral-small:latest"
    screen.set_model_from_selection()

    assert saved["set"] == ("llm", "model", "mistral-small:latest")
    assert saved["saved"] is True


def test_pull_requires_confirmation(monkeypatch) -> None:
    screen = OllamaConfigScreen()
    called = {"pull": False}

    def fake_pull(_name: str):
        called["pull"] = True

    def fake_confirm(_title: str, _msg: str, on_confirm: Callable, on_cancel=None):
        if on_cancel:
            on_cancel()

    monkeypatch.setattr(screen, "_pull_model", fake_pull)
    monkeypatch.setattr("view.ollama_config_screen.show_confirmation_dialog", fake_confirm)

    screen.selected_remote_model = "llama3.2:latest"
    screen.request_pull_selected_model()

    assert called["pull"] is False


def test_delete_requires_confirmation(monkeypatch) -> None:
    screen = OllamaConfigScreen()
    called = {"delete": False}

    def fake_delete(_name: str):
        called["delete"] = True

    def fake_confirm(_title: str, _msg: str, on_confirm: Callable, on_cancel=None):
        if on_cancel:
            on_cancel()

    monkeypatch.setattr(screen, "_delete_model", fake_delete)
    monkeypatch.setattr("view.ollama_config_screen.show_confirmation_dialog", fake_confirm)

    screen.selected_local_model = "mistral-small:latest"
    screen.request_delete_selected_model()

    assert called["delete"] is False


def test_pull_runs_when_confirmed(monkeypatch) -> None:
    screen = OllamaConfigScreen()
    _run_sync(screen)
    called = {"pull": False}

    def fake_pull(_name: str):
        called["pull"] = True

    def fake_confirm(_title: str, _msg: str, on_confirm: Callable, on_cancel=None):
        on_confirm()

    monkeypatch.setattr(screen, "_pull_model", fake_pull)
    monkeypatch.setattr(screen, "refresh_local_models", lambda: None)
    monkeypatch.setattr("view.ollama_config_screen.show_confirmation_dialog", fake_confirm)

    screen.selected_remote_model = "llama3.2:latest"
    screen.request_pull_selected_model()

    assert called["pull"] is True


def test_delete_runs_when_confirmed(monkeypatch) -> None:
    screen = OllamaConfigScreen()
    _run_sync(screen)
    called = {"delete": False}

    def fake_delete(_name: str):
        called["delete"] = True

    def fake_confirm(_title: str, _msg: str, on_confirm: Callable, on_cancel=None):
        on_confirm()

    monkeypatch.setattr(screen, "_delete_model", fake_delete)
    monkeypatch.setattr(screen, "refresh_local_models", lambda: None)
    monkeypatch.setattr("view.ollama_config_screen.show_confirmation_dialog", fake_confirm)

    screen.selected_local_model = "mistral-small:latest"
    screen.request_delete_selected_model()

    assert called["delete"] is True
