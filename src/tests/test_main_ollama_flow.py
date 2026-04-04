from __future__ import annotations

import importlib
import sys
from types import SimpleNamespace


def _load_main_module(monkeypatch):
    fake_window = SimpleNamespace(
        size=(1280, 720),
        bind=lambda *args, **kwargs: None,
        unbind=lambda *args, **kwargs: None,
    )
    monkeypatch.setattr("kivy.lang.Builder.load_file", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("util.paths.register_kivy_resource_paths", lambda: None)
    monkeypatch.setattr("kivy.core.window.Window", fake_window, raising=False)
    monkeypatch.setattr("kivymd.theming.Window", fake_window, raising=False)

    if "main" in sys.modules:
        return importlib.reload(sys.modules["main"])
    return importlib.import_module("main")


def test_startup_prompts_install_when_ollama_missing(monkeypatch) -> None:
    main_module = _load_main_module(monkeypatch)
    app = main_module.BatLLM()
    prompted = {"install": False}

    monkeypatch.setattr(
        main_module.ollama_service,
        "inspect_service_state",
        lambda: {"installed": False, "running": False},
    )
    monkeypatch.setattr(
        app,
        "_prompt_to_install_ollama",
        lambda: prompted.__setitem__("install", True),
    )

    app._run_startup_ollama_flow()

    assert prompted["install"] is True


def test_startup_auto_starts_ollama_when_enabled(monkeypatch) -> None:
    main_module = _load_main_module(monkeypatch)
    app = main_module.BatLLM()
    started = {"value": False}
    prompted = {"value": False}

    monkeypatch.setattr(
        main_module.config,
        "get",
        lambda section, key: True if (section, key) == ("ui", "auto_start_ollama") else None,
    )
    monkeypatch.setattr(
        app,
        "_start_ollama_in_background",
        lambda: started.__setitem__("value", True),
    )
    monkeypatch.setattr(
        app,
        "_prompt_to_start_ollama",
        lambda _model="": prompted.__setitem__("value", True),
    )

    app._handle_startup_ollama_state(
        {"installed": True, "running": False, "startup_model": "mistral-small:latest"}
    )

    assert started["value"] is True
    assert prompted["value"] is False


def test_startup_prompts_start_when_auto_start_disabled(monkeypatch) -> None:
    main_module = _load_main_module(monkeypatch)
    app = main_module.BatLLM()
    started = {"value": False}
    prompted = {"value": False}

    monkeypatch.setattr(
        main_module.config,
        "get",
        lambda section, key: False if (section, key) == ("ui", "auto_start_ollama") else None,
    )
    monkeypatch.setattr(
        app,
        "_start_ollama_in_background",
        lambda: started.__setitem__("value", True),
    )
    monkeypatch.setattr(
        app,
        "_prompt_to_start_ollama",
        lambda _model="": prompted.__setitem__("value", True),
    )

    app._handle_startup_ollama_state(
        {"installed": True, "running": False, "startup_model": "mistral-small:latest"}
    )

    assert started["value"] is False
    assert prompted["value"] is True


def test_prompt_to_start_includes_startup_model(monkeypatch) -> None:
    main_module = _load_main_module(monkeypatch)
    app = main_module.BatLLM()
    captured = {}

    monkeypatch.setattr(
        main_module,
        "show_confirmation_dialog",
        lambda title, message, on_confirm, on_cancel=None: captured.update(
            {"title": title, "message": message}
        ),
    )

    app._prompt_to_start_ollama("mistral-small:latest")

    assert captured["title"] == "Start Ollama"
    assert "BatLLM will warm: mistral-small:latest" in captured["message"]


def test_install_background_flow_rechecks_startup_when_install_completes(monkeypatch) -> None:
    main_module = _load_main_module(monkeypatch)
    app = main_module.BatLLM()
    handled = []
    refreshed = {"value": False}
    alerts = []

    monkeypatch.setattr(app, "_run_in_thread", lambda fn: fn())
    monkeypatch.setattr(main_module.Clock, "schedule_once", lambda callback, _dt=0: callback(0))
    monkeypatch.setattr(main_module.ollama_service, "install_service", lambda: (0, "installed"))
    monkeypatch.setattr(
        main_module.ollama_service,
        "inspect_service_state",
        lambda: {"installed": True, "running": False, "startup_model": "mistral-small:latest"},
    )
    monkeypatch.setattr(app, "_refresh_ollama_screen", lambda: refreshed.__setitem__("value", True))
    monkeypatch.setattr(app, "_handle_startup_ollama_state", lambda state: handled.append(state))
    monkeypatch.setattr(
        main_module,
        "show_fading_alert",
        lambda title, message, **_kwargs: alerts.append((title, message)),
    )

    app._install_ollama_in_background()

    assert refreshed["value"] is True
    assert handled == [{"installed": True, "running": False, "startup_model": "mistral-small:latest"}]
    assert alerts == [("Install Ollama", "installed")]


def test_on_stop_stops_ollama_when_enabled(monkeypatch) -> None:
    main_module = _load_main_module(monkeypatch)
    app = main_module.BatLLM()
    stopped = []

    monkeypatch.setattr(
        main_module.config,
        "get",
        lambda section, key: True if (section, key) == ("ui", "stop_ollama_on_exit") else None,
    )
    monkeypatch.setattr(
        main_module.ollama_service,
        "stop_service",
        lambda verbose=False: stopped.append(verbose) or 0,
    )

    app.on_stop()

    assert stopped == [False]
