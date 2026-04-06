from __future__ import annotations

from types import SimpleNamespace

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
        _remote_model_entries=[{"name": "all-minilm",
                                "display": "all-minilm (22m)", "size": "22m"}],
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
    assert opened["entries"] == [{"name": "all-minilm",
                                  "display": "all-minilm (22m)", "size": "22m"}]
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
                fake_screen._remote_model_display_map.get(
                    model_name, model_name) or "Select remote model",
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
    remembered = []
    fake_screen = SimpleNamespace(
        _managed_model_name=None,
        _set_status=lambda text: statuses.append(text),
        _append_log=lambda _text: None,
        _run_ollama_helper=lambda _action: DummyProc(returncode=0, stdout="ok"),
        _remember_served_model=lambda model: remembered.append(model),
        refresh_ollama_status=lambda: None,
        refresh_local_models=lambda: None,
        _run_in_thread=lambda fn: fn(),
    )

    monkeypatch.setattr(
        screen_module.config,
        "get",
        lambda _section, key: (
            "mistral-small:latest"
            if key == "last_served_model"
            else ("llama3.2:latest" if key == "model" else None)
        ),
    )

    screen_module.OllamaConfigScreen.start_ollama(fake_screen)

    assert fake_screen._managed_model_name == "mistral-small:latest"
    assert remembered == ["mistral-small:latest"]
    assert statuses[-1] == "Ollama started successfully."


def test_set_model_from_selection_saves_stops_previous_managed_and_serves(monkeypatch) -> None:
    saved = {"set": None, "saved": False}
    statuses = []
    refreshed = {"status": False, "local": False}
    stop_calls = []
    ensure_calls = []
    remembered = []

    fake_screen = SimpleNamespace(
        selected_local_model="llama3.2:latest",
        _managed_model_name="mistral-small:latest",
        _set_status=lambda text: statuses.append(text),
        _append_log=lambda _text: None,
        _run_in_thread=lambda fn: fn(),
        _get_running_model_names=lambda: ["mistral-small:latest"],
        _stop_serving_model=lambda model: stop_calls.append(model),
        _ensure_model_serving=lambda model: ensure_calls.append(model),
        _remember_served_model=lambda model: remembered.append(model),
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
    assert remembered == ["llama3.2:latest"]
    assert fake_screen._managed_model_name == "llama3.2:latest"
    assert refreshed["status"] is True


def test_build_ollama_install_command_is_platform_specific() -> None:
    assert screen_module.build_ollama_install_command("linux") == [
        "/bin/sh",
        "-lc",
        "export OLLAMA_NO_START=1; curl -fsSL https://ollama.com/install.sh | sh",
    ]
    assert screen_module.build_ollama_install_command("darwin") == [
        "/bin/sh",
        "-lc",
        "export OLLAMA_NO_START=1; curl -fsSL https://ollama.com/install.sh | sh",
    ]
    assert screen_module.build_ollama_install_command("win32") == [
        "powershell.exe",
        "-NoExit",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        "irm https://ollama.com/install.ps1 | iex",
    ]


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
        _remember_served_model=lambda _model: None,
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


def test_preload_model_uses_resolved_request_timeout(monkeypatch) -> None:
    calls = []
    resolved = {}

    class FakeResponse:
        content = b"{}"

        def raise_for_status(self):
            return None

        def json(self):
            return {"ok": True}

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse()

    fake_screen = SimpleNamespace(
        _llm_endpoint=lambda: ("http://localhost", 11434),
        _append_log=lambda _text: None,
        _llm_timeout_config=lambda model_name: {"model": model_name, "timeout": "180"},
    )

    monkeypatch.setattr(screen_module.requests, "post", fake_post)
    monkeypatch.setattr(
        screen_module.ollama_service,
        "resolve_request_timeout",
        lambda _cfg, *, model=None: resolved.update({"cfg": _cfg, "model": model}) or 180.0,
    )

    result = screen_module.OllamaConfigScreen._preload_model(fake_screen, "test-model")

    assert result == {"ok": True}
    assert resolved == {"cfg": {"model": "test-model", "timeout": "180"}, "model": "test-model"}
    assert len(calls) == 1
    assert calls[0][0] == "http://localhost:11434/api/generate"
    assert calls[0][1]["timeout"] == 180.0
    assert calls[0][1]["json"] == {"model": "test-model", "keep_alive": "30m"}


def test_local_selection_refreshes_timeout_editor_from_model_override(monkeypatch) -> None:
    monkeypatch.setattr(
        screen_module.config,
        "get",
        lambda section, key: {
            ("llm", "last_served_model"): "",
            ("llm", "model"): "qwen3:30b",
            ("llm", "timeout"): None,
            ("llm", "model_timeouts"): {"qwen3:30b": 180.0},
        }.get((section, key)),
    )

    screen = screen_module.OllamaConfigScreen()
    screen._set_local_selection("qwen3:30b")

    assert screen.selected_local_timeout_text == "180"
    assert "saved per-model override" in screen.selected_local_timeout_details


def test_save_selected_model_timeout_persists_override(monkeypatch) -> None:
    config_state = {
        ("llm", "last_served_model"): "",
        ("llm", "model"): "qwen3:30b",
        ("llm", "timeout"): None,
        ("llm", "model_timeouts"): {},
    }
    save_calls = []

    monkeypatch.setattr(screen_module.Clock, "schedule_once", lambda callback, _dt=0: callback(0))
    monkeypatch.setattr(screen_module.config, "get", lambda section,
                        key: config_state.get((section, key)))
    monkeypatch.setattr(
        screen_module.config,
        "set",
        lambda section, key, value: config_state.__setitem__((section, key), value),
    )
    monkeypatch.setattr(screen_module.config, "save", lambda: save_calls.append(True))
    monkeypatch.setattr(screen_module, "show_fading_alert", lambda *_args, **_kwargs: None)

    screen = screen_module.OllamaConfigScreen()
    screen._set_local_selection("qwen3:30b")
    screen.selected_local_timeout_text = "150"

    screen.save_selected_model_timeout()

    assert config_state[("llm", "model_timeouts")] == {"qwen3:30b": 150.0}
    assert save_calls == [True]
    assert screen.status_text == "Saved timeout for qwen3:30b."
    assert screen.selected_local_timeout_text == "150"
    assert "saved per-model override" in screen.selected_local_timeout_details


def test_reset_selected_model_timeout_uses_common_model_default(monkeypatch) -> None:
    config_state = {
        ("llm", "last_served_model"): "",
        ("llm", "model"): "qwen3:30b",
        ("llm", "timeout"): None,
        ("llm", "model_timeouts"): {"qwen3:30b": 150.0},
    }
    save_calls = []

    monkeypatch.setattr(screen_module.Clock, "schedule_once", lambda callback, _dt=0: callback(0))
    monkeypatch.setattr(screen_module.config, "get", lambda section,
                        key: config_state.get((section, key)))
    monkeypatch.setattr(
        screen_module.config,
        "set",
        lambda section, key, value: config_state.__setitem__((section, key), value),
    )
    monkeypatch.setattr(screen_module.config, "save", lambda: save_calls.append(True))
    monkeypatch.setattr(screen_module, "show_fading_alert", lambda *_args, **_kwargs: None)

    screen = screen_module.OllamaConfigScreen()
    screen._set_local_selection("qwen3:30b")

    screen.reset_selected_model_timeout()

    assert config_state[("llm", "model_timeouts")] == {}
    assert save_calls == [True]
    assert screen.status_text == "Using default timeout for qwen3:30b."
    assert screen.selected_local_timeout_text == "120"
    assert "common-model default" in screen.selected_local_timeout_details


def test_request_delete_selected_model_clears_timeout_override(monkeypatch) -> None:
    removed = []
    deleted = []
    refreshed = []

    fake_screen = SimpleNamespace(
        selected_local_model="qwen3:30b",
        _managed_model_name=None,
        _set_status=lambda _text: None,
        _append_log=lambda _text: None,
        _run_in_thread=lambda fn: fn(),
        _delete_model=lambda model: deleted.append(model),
        _remove_model_timeout_override=lambda model: removed.append(model) or True,
        refresh_local_models=lambda: refreshed.append(True),
    )

    monkeypatch.setattr(
        screen_module,
        "show_confirmation_dialog",
        lambda _title, _text, on_confirm, on_cancel: on_confirm(),
    )

    screen_module.OllamaConfigScreen.request_delete_selected_model(fake_screen)

    assert deleted == ["qwen3:30b"]
    assert removed == ["qwen3:30b"]
    assert refreshed == [True]
