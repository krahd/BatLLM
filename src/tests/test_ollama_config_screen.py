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
    setattr(screen, "_run_in_thread", lambda fn: fn())


def _run_clock_now(monkeypatch) -> None:
    monkeypatch.setattr("view.ollama_config_screen.Clock.schedule_once",
                        lambda callback, _dt=0: callback(0))


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


def test_start_and_stop_call_scripts(monkeypatch) -> None:
    screen = OllamaConfigScreen()
    calls = []
    _run_sync(screen)
    _run_clock_now(monkeypatch)

    def fake_run_script(script_name: str, *args: str):
        calls.append((script_name, args))
        return DummyProc(returncode=0, stdout="ok", stderr="")

    setattr(screen, "_run_script", fake_run_script)
    monkeypatch.setattr(screen, "refresh_ollama_status", lambda: None)
    monkeypatch.setattr(screen, "refresh_local_models", lambda: None)

    screen.start_ollama()
    screen.stop_ollama()

    assert ("start_ollama.sh", ()) in calls
    assert ("stop_ollama.sh", ("-v",)) in calls
    assert "./start_ollama.sh" in screen.output_log
    assert "./stop_ollama.sh -v" in screen.output_log
    assert "ok" in screen.output_log


def test_start_failure_prompts_install_guidance(monkeypatch) -> None:
    screen = OllamaConfigScreen()
    _run_sync(screen)
    prompted = {"value": False}
    _run_clock_now(monkeypatch)

    setattr(screen, "_run_script", lambda *_args, **_kwargs: DummyProc(
        returncode=1,
        stdout="",
        stderr="ollama: command not found",
    ))
    setattr(screen, "_open_install_guidance", lambda: prompted.__setitem__("value", True))

    screen.start_ollama()

    assert prompted["value"] is True
    assert "ollama: command not found" in screen.output_log


def test_format_status_report_when_ollama_missing() -> None:
    screen = OllamaConfigScreen()

    report = getattr(screen, "_format_status_report")(
        {
            "found": False,
            "version": "",
            "running": False,
            "server_version": "",
            "running_models": [],
            "configured_model": "mistral-small:latest",
        }
    )

    assert "Ollama CLI: not found" in report
    assert "Installed version: unavailable" in report
    assert "Server status: not running" in report
    assert "BatLLM model: mistral-small:latest" in report


def test_refresh_status_reports_running_model(monkeypatch) -> None:
    screen = OllamaConfigScreen()
    _run_sync(screen)
    _run_clock_now(monkeypatch)

    monkeypatch.setattr(
        screen,
        "_collect_ollama_status",
        lambda: {
            "found": True,
            "version": "ollama version is 0.18.2",
            "running": True,
            "server_version": "0.18.2",
            "running_models": ["mistral-small:latest"],
            "configured_model": "mistral-small:latest",
        },
    )

    screen.refresh_ollama_status()

    assert "Installed version: ollama version is 0.18.2" in screen.status_details
    assert "Server status: running" in screen.status_details
    assert "Running models: mistral-small:latest" in screen.status_details
    assert "BatLLM model: mistral-small:latest (running)" in screen.status_details


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

    def fake_confirm(_title: str, _msg: str, on_confirm: Callable | None = None, on_cancel=None, **_kwargs):
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

    def fake_confirm(_title: str, _msg: str, on_confirm: Callable | None = None, on_cancel=None, **_kwargs):
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

    def fake_confirm(_title: str, _msg: str, on_confirm: Callable | None = None, _on_cancel=None, **_kwargs):
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

    def fake_confirm(_title: str, _msg: str, on_confirm: Callable | None = None, _on_cancel=None, **_kwargs):
        on_confirm()

    monkeypatch.setattr(screen, "_delete_model", fake_delete)
    monkeypatch.setattr(screen, "refresh_local_models", lambda: None)
    monkeypatch.setattr("view.ollama_config_screen.show_confirmation_dialog", fake_confirm)

    screen.selected_local_model = "mistral-small:latest"
    screen.request_delete_selected_model()

    assert called["delete"] is True
