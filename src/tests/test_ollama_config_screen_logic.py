from __future__ import annotations

from types import SimpleNamespace

import requests

from view import ollama_config_screen as screen_module


class DummyProc:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_parse_remote_models_html_extracts_display_names_with_sizes() -> None:
    html = """
    <a href="/library/all-minilm" class="group w-full space-y-5">
      <span x-test-size>22m</span>
    </a>
    <a href="/library/smollm2" class="group w-full space-y-5">
      <span x-test-size>135m</span>
    </a>
    <a href="/library/all-minilm" class="group w-full space-y-5">
      <span x-test-size>22m</span>
    </a>
    """

    entries = screen_module.OllamaConfigScreen._parse_remote_models_html(None, html)

    assert entries == [
        {"name": "all-minilm", "display": "all-minilm (22m)", "size": "22m"},
        {"name": "smollm2", "display": "smollm2 (135m)", "size": "135m"},
    ]


def test_open_local_model_selector_refreshes_then_opens_picker() -> None:
    refreshed = {"value": False}
    opened = {"title": None, "entries": None, "selected": None}
    logs = []

    def fake_refresh_local_models(on_complete=None):
        refreshed["value"] = True
        if on_complete:
            on_complete()

    fake_screen = SimpleNamespace(
        _append_log=lambda text: logs.append(text),
        refresh_local_models=fake_refresh_local_models,
        _current_model_entries=lambda entries, models: entries if entries else models,
        _local_model_entries=[{"name": "llama3.2:latest", "display": "llama3.2:latest"}],
        local_models=["llama3.2:latest"],
        selected_local_model="llama3.2:latest",
        _select_local_model=lambda _model: None,
        _show_model_picker=lambda **kwargs: opened.update(
            {
                "title": kwargs["title"],
                "entries": kwargs["entries"],
                "selected": kwargs["selected_value"],
            }
        ),
    )

    screen_module.OllamaConfigScreen.open_local_model_selector(fake_screen)

    assert refreshed["value"] is True
    assert logs == ["Refreshing local models..."]
    assert opened["title"] == "Local Models"
    assert opened["entries"] == [{"name": "llama3.2:latest", "display": "llama3.2:latest"}]
    assert opened["selected"] == "llama3.2:latest"


def test_open_remote_model_selector_refreshes_then_opens_picker() -> None:
    refreshed = {"value": False}
    opened = {"title": None, "entries": None, "selected": None}
    logs = []

    def fake_refresh_remote_models(on_complete=None):
        refreshed["value"] = True
        if on_complete:
            on_complete()

    fake_screen = SimpleNamespace(
        _append_log=lambda text: logs.append(text),
        refresh_remote_models=fake_refresh_remote_models,
        _current_model_entries=lambda entries, models: entries if entries else models,
        _remote_model_entries=[{"name": "all-minilm", "display": "all-minilm (22m)", "size": "22m"}],
        remote_models=["all-minilm"],
        selected_remote_model="all-minilm",
        _select_remote_model=lambda _model: None,
        _show_model_picker=lambda **kwargs: opened.update(
            {
                "title": kwargs["title"],
                "entries": kwargs["entries"],
                "selected": kwargs["selected_value"],
            }
        ),
    )

    screen_module.OllamaConfigScreen.open_remote_model_selector(fake_screen)

    assert refreshed["value"] is True
    assert logs == ["Refreshing remote models..."]
    assert opened["title"] == "Remote Models"
    assert opened["entries"] == [{"name": "all-minilm", "display": "all-minilm (22m)", "size": "22m"}]
    assert opened["selected"] == "all-minilm"


def test_refresh_all_refreshes_status_and_both_lists() -> None:
    calls = []
    logs = []
    fake_screen = SimpleNamespace(
        _append_log=lambda text: logs.append(text),
        refresh_ollama_status=lambda: calls.append("status"),
        refresh_local_models=lambda: calls.append("local"),
        refresh_remote_models=lambda: calls.append("remote"),
    )

    screen_module.OllamaConfigScreen.refresh_all(fake_screen)

    assert logs == ["Refreshing..."]
    assert calls == ["status", "local", "remote"]


def test_refresh_remote_models_uses_official_library_html(monkeypatch) -> None:
    fake_screen = SimpleNamespace(
        remote_models=[],
        selected_remote_model="",
        selected_remote_model_label="Select remote model",
        _remote_model_entries=[],
        _remote_model_display_map={},
        _set_status=lambda _text: None,
        _append_log=lambda _text: None,
        _schedule_ui_callback=lambda callback: callback() if callback else None,
        _run_in_thread=lambda fn: fn(),
        _set_remote_selection=lambda model_name: (
            setattr(fake_screen, "selected_remote_model", model_name),
            setattr(
                fake_screen,
                "selected_remote_model_label",
                fake_screen._remote_model_display_map.get(model_name, model_name) or "Select remote model",
            ),
        ),
        _parse_remote_models_html=lambda html: screen_module.OllamaConfigScreen._parse_remote_models_html(
            None, html
        ),
    )

    def fake_schedule_once(callback, _dt=0):
        callback(0)

    class FakeResponse:
        text = """
        <a href="/library/all-minilm" class="group w-full space-y-5">
          <span x-test-size>22m</span>
        </a>
        <a href="/library/smollm2" class="group w-full space-y-5">
          <span x-test-size>135m</span>
        </a>
        """

        def raise_for_status(self):
            return None

    monkeypatch.setattr(screen_module.Clock, "schedule_once", fake_schedule_once)
    monkeypatch.setattr(screen_module.requests, "get", lambda _url, timeout=12: FakeResponse())

    screen_module.OllamaConfigScreen.refresh_remote_models(fake_screen)

    assert fake_screen.remote_models == ["all-minilm", "smollm2"]
    assert fake_screen.selected_remote_model == "all-minilm"
    assert fake_screen.selected_remote_model_label == "all-minilm (22m)"
    assert fake_screen._remote_model_entries[0]["display"] == "all-minilm (22m)"


def test_refresh_local_models_preserves_unsaved_selection(monkeypatch) -> None:
    fake_screen = SimpleNamespace(
        selected_local_model="llama3.2:latest",
        selected_local_model_label="llama3.2:latest",
        local_models=[],
        _local_model_entries=[],
        _set_status=lambda _text: None,
        _append_log=lambda _text: None,
        _schedule_ui_callback=lambda callback: callback() if callback else None,
        _run_in_thread=lambda fn: fn(),
        _llm_endpoint=lambda: ("http://localhost", 11434),
        _json_get=lambda _url, timeout=8: {
            "models": [{"name": "llama3.2:latest"}, {"name": "mistral-small:latest"}]
        },
        _set_local_selection=lambda model_name: (
            setattr(fake_screen, "selected_local_model", model_name),
            setattr(fake_screen, "selected_local_model_label", model_name or "Select local model"),
        ),
    )

    monkeypatch.setattr(screen_module.Clock, "schedule_once", lambda callback, _dt=0: callback(0))
    monkeypatch.setattr(screen_module.config, "get", lambda _section, _key: "mistral-small:latest")

    screen_module.OllamaConfigScreen.refresh_local_models(fake_screen)

    assert fake_screen.selected_local_model == "llama3.2:latest"
    assert fake_screen.selected_local_model_label == "llama3.2:latest"


def test_start_ollama_marks_configured_model_as_managed(monkeypatch) -> None:
    statuses = []
    fake_screen = SimpleNamespace(
        _managed_model_name=None,
        _set_status=lambda text: statuses.append(text),
        _append_log=lambda _text: None,
        _run_ollama_helper=lambda _action: DummyProc(returncode=0, stdout="ok"),
        refresh_ollama_status=lambda: None,
        refresh_local_models=lambda: None,
        _run_in_thread=lambda fn: fn(),
    )

    monkeypatch.setattr(screen_module.config, "get", lambda _section, key: "llama3.2:latest" if key == "model" else None)

    screen_module.OllamaConfigScreen.start_ollama(fake_screen)

    assert fake_screen._managed_model_name == "llama3.2:latest"
    assert statuses[-1] == "Ollama started successfully."


def test_set_model_from_selection_saves_stops_previous_managed_and_serves(monkeypatch) -> None:
    saved = {"set": None, "saved": False}
    statuses = []
    refreshed = {"status": False, "local": False}
    stop_calls = []
    ensure_calls = []

    fake_screen = SimpleNamespace(
        selected_local_model="llama3.2:latest",
        _managed_model_name="mistral-small:latest",
        _set_status=lambda text: statuses.append(text),
        _append_log=lambda _text: None,
        _run_in_thread=lambda fn: fn(),
        _get_running_model_names=lambda: ["mistral-small:latest"],
        _stop_serving_model=lambda model: stop_calls.append(model),
        _ensure_model_serving=lambda model: ensure_calls.append(model),
        refresh_ollama_status=lambda: refreshed.__setitem__("status", True),
        refresh_local_models=lambda: refreshed.__setitem__("local", True),
    )

    monkeypatch.setattr(
        screen_module.config,
        "set",
        lambda section, key, value: saved.__setitem__("set", (section, key, value)),
    )
    monkeypatch.setattr(screen_module.config, "save", lambda: saved.__setitem__("saved", True))

    screen_module.OllamaConfigScreen.set_model_from_selection(fake_screen)

    assert saved["set"] == ("llm", "model", "llama3.2:latest")
    assert saved["saved"] is True
    assert stop_calls == ["mistral-small:latest"]
    assert ensure_calls == ["llama3.2:latest"]
    assert fake_screen._managed_model_name == "llama3.2:latest"
    assert refreshed["status"] is True
    assert refreshed["local"] is True
    assert statuses[-1] == "Model ready: llama3.2:latest"


def test_set_model_from_selection_does_not_manage_external_running_model(monkeypatch) -> None:
    fake_screen = SimpleNamespace(
        selected_local_model="llama3.2:latest",
        _managed_model_name=None,
        _set_status=lambda _text: None,
        _append_log=lambda _text: None,
        _run_in_thread=lambda fn: fn(),
        _get_running_model_names=lambda: ["llama3.2:latest"],
        _stop_serving_model=lambda _model: None,
        _ensure_model_serving=lambda _model: None,
        refresh_ollama_status=lambda: None,
        refresh_local_models=lambda: None,
    )

    monkeypatch.setattr(screen_module.config, "set", lambda *_args: None)
    monkeypatch.setattr(screen_module.config, "save", lambda: None)

    screen_module.OllamaConfigScreen.set_model_from_selection(fake_screen)

    assert fake_screen._managed_model_name is None


def test_set_model_from_selection_alerts_when_empty(monkeypatch) -> None:
    alerted = {"value": False}
    fake_screen = SimpleNamespace(selected_local_model="   ")

    monkeypatch.setattr(
        screen_module,
        "show_fading_alert",
        lambda *_args, **_kwargs: alerted.__setitem__("value", True),
    )

    screen_module.OllamaConfigScreen.set_model_from_selection(fake_screen)

    assert alerted["value"] is True
