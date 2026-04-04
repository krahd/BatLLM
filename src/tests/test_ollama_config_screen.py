from __future__ import annotations

from typing import Callable

from view.history_screen import HistoryScreen
from view.ollama_config_screen import OllamaConfigScreen
from view.settings_screen import SettingsScreen


class DummyProc:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class DummyTransition:
    def __init__(self, direction: str = "left"):
        self.direction = direction


class DummyManager:
    def __init__(self, current: str = "settings"):
        self.current = current
        self.transition = DummyTransition()


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
    assert screen.manager.transition.direction == "left"


def test_ollama_screen_navigates_back_to_settings() -> None:
    screen = OllamaConfigScreen()
    screen.manager = DummyManager(current="ollama_config")

    screen.go_to_settings_screen()

    assert screen.manager.current == "settings"
    assert screen.manager.transition.direction == "right"


def test_ollama_screen_escape_returns_to_settings() -> None:
    screen = OllamaConfigScreen()
    screen.manager = DummyManager(current="ollama_config")

    assert screen.handle_window_key_down(None, 27) is True
    assert screen.manager.current == "settings"
    assert screen.manager.transition.direction == "right"


def test_ollama_screen_escape_dismisses_model_picker_before_navigating() -> None:
    screen = OllamaConfigScreen()
    screen.manager = DummyManager(current="ollama_config")
    dismissed = {"value": False}

    class DummyPopup:
        def dismiss(self):
            dismissed["value"] = True

    screen._model_picker_popup = DummyPopup()

    assert screen.handle_window_key_down(None, 27) is True
    assert dismissed["value"] is True
    assert screen.manager.current == "ollama_config"


def test_history_screen_back_navigates_right() -> None:
    screen = HistoryScreen()
    screen.manager = DummyManager(current="history")

    screen.go_back_home()

    assert screen.manager.current == "home"
    assert screen.manager.transition.direction == "right"


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
    _run_sync(screen)

    def fake_set(section: str, key: str, value: str):
        saved["set"] = (section, key, value)

    def fake_save():
        saved["saved"] = True

    monkeypatch.setattr("view.ollama_config_screen.config.set", fake_set)
    monkeypatch.setattr("view.ollama_config_screen.config.save", fake_save)
    monkeypatch.setattr(screen, "_get_running_model_names", lambda: [])
    monkeypatch.setattr(screen, "_ensure_model_serving", lambda _model: None)
    monkeypatch.setattr(screen, "refresh_ollama_status", lambda: None)
    monkeypatch.setattr(screen, "refresh_local_models", lambda: None)

    screen.selected_local_model = "mistral-small:latest"
    screen.set_model_from_selection()

    assert saved["set"] == ("llm", "model", "mistral-small:latest")
    assert saved["saved"] is True


def test_pull_requires_confirmation(monkeypatch) -> None:
    screen = OllamaConfigScreen()
    called = {"pull": False}

    def fake_pull(_name: str):
        called["pull"] = True

    def fake_confirm(_title: str, _msg: str, _on_confirm: Callable | None = None, on_cancel=None, **_kwargs):
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

    def fake_confirm(_title: str, _msg: str, _on_confirm: Callable | None = None, on_cancel=None, **_kwargs):
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


def test_show_model_picker_uses_touching_rows_with_white_text(monkeypatch) -> None:
    screen = OllamaConfigScreen()
    monkeypatch.setattr("view.ollama_config_screen.dp", lambda value: value)

    class FakeContainer:
        def __init__(self, **kwargs):
            self.children = []
            for key, value in kwargs.items():
                if key == "spacing" and not isinstance(value, (list, tuple)):
                    value = (value, value)
                setattr(self, key, value)

        def add_widget(self, widget):
            self.children.append(widget)

        def bind(self, **_kwargs):
            return None

        def setter(self, name):
            return lambda _instance, value: setattr(self, name, value)

    class FakeButton(FakeContainer):
        pass

    class FakePopup:
        def __init__(self, **kwargs):
            self.title = kwargs["title"]
            self.content = kwargs["content"]
            self.size_hint = kwargs["size_hint"]
            self.auto_dismiss = kwargs["auto_dismiss"]
            self._bindings = {}

        def bind(self, **kwargs):
            self._bindings.update(kwargs)

        def dismiss(self):
            callback = self._bindings.get("on_dismiss")
            if callback is not None:
                callback(self)

        def open(self):
            return None

    monkeypatch.setattr("view.ollama_config_screen.BoxLayout", FakeContainer)
    monkeypatch.setattr("view.ollama_config_screen.ScrollView", FakeContainer)
    monkeypatch.setattr("view.ollama_config_screen.GridLayout", FakeContainer)
    monkeypatch.setattr("view.ollama_config_screen.Button", FakeButton)
    monkeypatch.setattr("view.ollama_config_screen.Popup", FakePopup)

    screen._show_model_picker(
        title="Remote Models",
        entries=[
            {"name": "all-minilm", "display": "all-minilm (22m)", "size": "22m"},
            {"name": "smollm2", "display": "smollm2 (135m)", "size": "135m"},
        ],
        selected_value="all-minilm",
        on_select=lambda _model: None,
    )

    popup = screen._model_picker_popup
    assert popup is not None
    assert popup.auto_dismiss is True

    layout = popup.content
    scroll = next(child for child in layout.children if isinstance(child, FakeContainer) and hasattr(child, "do_scroll_x"))
    items = scroll.children[0]
    buttons = {button.text: button for button in items.children}

    assert tuple(items.spacing) == (0, 0)
    assert tuple(buttons["all-minilm (22m)"].color) == (1, 1, 1, 1)
    assert tuple(buttons["smollm2 (135m)"].color) == (1, 1, 1, 1)
