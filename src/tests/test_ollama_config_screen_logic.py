from __future__ import annotations

from types import SimpleNamespace

from view import ollama_config_screen as screen_module


class DummyProc:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


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


def test_refresh_remote_models_uses_modelito_catalog(monkeypatch) -> None:
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
    )

    def fake_schedule_once(callback, _dt=0):
        callback(0)

    class FakeEntry:
        def __init__(self, name: str, *, installed: bool = False, raw=None):
            self.name = name
            self.installed = installed
            self.raw = raw or {}

    monkeypatch.setattr(screen_module.Clock, "schedule_once", fake_schedule_once)
    monkeypatch.setattr(
        screen_module.modelito_ollama_service,
        "list_remote_model_catalog",
        lambda: [
            FakeEntry("all-minilm", raw={"parameter_size": "22m"}),
            FakeEntry("smollm2", installed=True, raw={"parameter_size": "135m"}),
        ],
    )

    screen_module.OllamaConfigScreen.refresh_remote_models(fake_screen)

    assert fake_screen.remote_models == ["all-minilm", "smollm2"]
    assert fake_screen.selected_remote_model == "all-minilm"
    assert fake_screen.selected_remote_model_label == "all-minilm (22m)"
    assert fake_screen._remote_model_entries[0]["display"] == "all-minilm (22m)"
    assert fake_screen._remote_model_entries[1]["display"] == "smollm2 (135m) [installed]"


def test_remote_selection_refreshes_timeout_details(monkeypatch) -> None:
    monkeypatch.setattr(
        screen_module.ollama_service,
        "estimate_remote_model_timeout_details",
        lambda model_name, *, size_label="": (150.0, "the Qwen 3 family rule"),
    )

    screen = screen_module.OllamaConfigScreen()
    screen._remote_model_entries = [{"name": "qwen3", "display": "qwen3 (30b)", "size": "30b"}]
    screen._remote_model_display_map = {"qwen3": "qwen3 (30b)"}

    screen._set_remote_selection("qwen3")

    assert screen.selected_remote_model_label == "qwen3 (30b)"
    assert "150s" in screen.selected_remote_timeout_details
    assert "Qwen 3 family rule" in screen.selected_remote_timeout_details


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
        _set_local_selection=lambda model_name: (
            setattr(fake_screen, "selected_local_model", model_name),
            setattr(fake_screen, "selected_local_model_label", model_name or "Select local model"),
        ),
    )

    monkeypatch.setattr(screen_module.Clock, "schedule_once", lambda callback, _dt=0: callback(0))
    monkeypatch.setattr(screen_module.config, "get", lambda _section, _key: "mistral-small:latest")
    monkeypatch.setattr(
        screen_module.modelito_ollama_service,
        "list_local_models",
        lambda: ["llama3.2:latest", "mistral-small:latest"],
    )

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
        _run_ollama_helper=lambda *_args: DummyProc(returncode=0, stdout="ok"),
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
        "brew",
        "install",
        "ollama",
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

    fake_screen = SimpleNamespace(
        _llm_endpoint=lambda: ("http://localhost", 11434),
        _append_log=lambda _text: None,
        _llm_timeout_config=lambda model_name: {"model": model_name, "timeout": "180"},
    )

    monkeypatch.setattr(
        screen_module.ollama_service,
        "preload_model",
        lambda base_url, port, model_name, timeout=120.0: calls.append(
            (base_url, port, model_name, timeout)
        ),
    )
    monkeypatch.setattr(
        screen_module.ollama_service,
        "resolve_request_timeout",
        lambda _cfg, *, model=None: resolved.update({"cfg": _cfg, "model": model}) or 180.0,
    )

    result = screen_module.OllamaConfigScreen._preload_model(fake_screen, "test-model")

    assert result == {"ok": True, "model": "test-model", "timeout": 180.0}
    assert resolved == {"cfg": {"model": "test-model", "timeout": "180"}, "model": "test-model"}
    assert len(calls) == 1
    assert calls[0] == ("http://localhost", 11434, "test-model", 180.0)


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


def test_save_warmup_timeout_persists_override(monkeypatch) -> None:
    config_state = {
        ("llm", "last_served_model"): "",
        ("llm", "model"): "qwen3:30b",
        ("llm", "warmup_timeout"): 30.0,
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
    screen.warmup_timeout_text = "45"

    screen.save_warmup_timeout()

    assert config_state[("llm", "warmup_timeout")] == 45.0
    assert save_calls == [True]
    assert screen.status_text == "Saved warmup timeout."
    assert "45s" in screen.warmup_timeout_details


def test_reset_warmup_timeout_uses_default(monkeypatch) -> None:
    config_state = {
        ("llm", "last_served_model"): "",
        ("llm", "model"): "qwen3:30b",
        ("llm", "warmup_timeout"): 45.0,
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

    screen = screen_module.OllamaConfigScreen()
    screen.reset_warmup_timeout()

    assert config_state[("llm", "warmup_timeout")] is None
    assert save_calls == [True]
    assert screen.status_text == "Using default warmup timeout."
    assert "30s" in screen.warmup_timeout_details


def test_start_ollama_passes_configured_warmup_timeout(monkeypatch) -> None:
    statuses = []
    helper_calls = []
    remembered = []
    fake_screen = SimpleNamespace(
        _managed_model_name=None,
        _set_status=lambda text: statuses.append(text),
        _append_log=lambda _text: None,
        _run_ollama_helper=lambda *args: helper_calls.append(
            args) or DummyProc(returncode=0, stdout="ok"),
        _remember_served_model=lambda model: remembered.append(model),
        refresh_ollama_status=lambda: None,
        refresh_local_models=lambda: None,
        _run_in_thread=lambda fn: fn(),
        _warmup_timeout_config=lambda: {"warmup_timeout": 45.0},
    )

    monkeypatch.setattr(
        screen_module.ollama_service,
        "resolve_warmup_timeout",
        lambda _cfg: 45.0,
    )
    monkeypatch.setattr(
        screen_module.config,
        "get",
        lambda _section, key: "mistral-small:latest" if key == "last_served_model" else "llama3.2:latest",
    )

    screen_module.OllamaConfigScreen.start_ollama(fake_screen)

    assert helper_calls == [("start", "--warmup-timeout", "45")]
    assert remembered == ["mistral-small:latest"]
    assert statuses[-1] == "Ollama started successfully."


def test_ensure_model_serving_uses_detailed_result_success(monkeypatch) -> None:
    logs = []
    fake_screen = SimpleNamespace(
        _llm_endpoint=lambda: ("http://localhost", 11434),
        _llm_timeout_config=lambda model_name: {"model": model_name, "timeout": 120},
        _append_log=lambda text: logs.append(text),
    )

    monkeypatch.setattr(screen_module.ollama_service, "resolve_request_timeout",
                        lambda _cfg, *, model=None: 120.0)
    monkeypatch.setattr(
        screen_module.modelito_ollama_service,
        "ensure_model_ready_detailed",
        lambda *args, **kwargs: SimpleNamespace(
            success=True,
            phase="ready",
            elapsed_seconds=1.25,
            source="probe",
            message="ready",
            error=None,
        ),
    )

    result = screen_module.OllamaConfigScreen._ensure_model_serving(fake_screen, "smollm2")

    assert result == {"ready": True}
    assert any("phase=ready" in entry and "source=probe" in entry for entry in logs)


def test_ensure_model_serving_uses_detailed_result_failure(monkeypatch) -> None:
    fake_screen = SimpleNamespace(
        _llm_endpoint=lambda: ("http://localhost", 11434),
        _llm_timeout_config=lambda model_name: {"model": model_name, "timeout": 120},
        _append_log=lambda _text: None,
    )

    monkeypatch.setattr(screen_module.ollama_service, "resolve_request_timeout",
                        lambda _cfg, *, model=None: 120.0)
    monkeypatch.setattr(
        screen_module.modelito_ollama_service,
        "ensure_model_ready_detailed",
        lambda *args, **kwargs: SimpleNamespace(
            success=False,
            phase="failed",
            elapsed_seconds=0.4,
            source="probe",
            message="warmup failed",
            error="timed out waiting for readiness",
        ),
    )

    try:
        screen_module.OllamaConfigScreen._ensure_model_serving(fake_screen, "smollm2")
    except RuntimeError as exc:
        assert "timed out waiting for readiness" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when detailed readiness fails")
