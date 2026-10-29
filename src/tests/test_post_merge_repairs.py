"""Regression coverage for the eleven post-merge audit findings."""
from copy import deepcopy
from importlib import import_module, util as import_util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import MappingProxyType, SimpleNamespace
import zipfile

import pytest

from configs.app_config import AppConfig, config
from game.ollama_connector import OllamaConnector
from game.replay_engine import GameplaySettingsSnapshot
from game.session_schema import SessionFormatError, load_session_payload, validate_session_payload
from game.trace_verifier import verify_file, verify_payload
from llm import service
from modelito.exceptions import ModelitoTimeoutError
from tests.test_adversarial_audit import wire_server  # shared test-owned HTTP fixture
from tests.test_game_analyzer import _sample_payload
from tests.test_gameplay_deterministic import _build_board, _complete_scheduled_turn
from tests.test_trace_contract import build
from view.ollama_config_screen import OllamaConfigScreen
from view.settings_screen import SettingsScreen


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def editor(monkeypatch):
    monkeypatch.setattr("kivy.core.window.Window", SimpleNamespace(), raising=False)
    return import_module("configs.configurator")


def _temporary_settings():
    ids = SimpleNamespace(**{
        key: SimpleNamespace(value=value) for key, value in {
            "rounds_slider": 9, "turns_slider": 3, "health_slider": 30,
            "damage_slider": 5, "shield_slider": 70, "step_slider": 0.03,
        }.items()
    }, **{
        key: SimpleNamespace(active=True) for key in (
            "independent_checkbox", "augmentation_checkbox", "confirm_on_exit_checkbox",
            "save_on_exit_checkbox", "auto_start_ollama_checkbox", "stop_ollama_on_exit_checkbox",
        )
    })
    screen = SimpleNamespace(ids=ids, go_to_home_screen=lambda: None)
    screen.update_config = lambda **kwargs: SettingsScreen.update_config(screen, **kwargs)
    SettingsScreen.set_and_return(screen)


def test_temporary_settings_survive_incidental_saves_without_becoming_defaults(monkeypatch):
    config.set("game", "total_rounds", 2)
    config.set("llm", "last_served_model", "")
    config.save()
    _temporary_settings()
    connector = OllamaConnector()
    monkeypatch.setattr(connector.client, "chat", lambda **k: {"message": {"content": "M"}})
    connector.send_prompt_to_llm_sync(1, user_text="advance", game_state={})
    config.set("llm", "model_timeouts", {"test": 70})
    config.save()
    assert config.get("game", "total_rounds") == 9
    saved = AppConfig(path=config._path)
    assert saved.get("game", "total_rounds") == 2
    assert saved.get("ui", "auto_start_ollama") is False
    assert saved.get("llm", "model_timeouts") == {"test": 70}


def test_explicit_defaults_replace_temporary_overrides():
    preferences = AppConfig(path=config._path)
    preferences.set_temporary("game", "total_rounds", 9)
    preferences.set("game", "total_rounds", 4)
    preferences.save()
    assert preferences.get("game", "total_rounds") == 4
    assert AppConfig(path=config._path).get("game", "total_rounds") == 4


@pytest.mark.parametrize("after_turn", [False, True])
def test_reset_retires_initial_and_next_turn_callbacks(monkeypatch, after_turn):
    board, scheduled, _ = _build_board(monkeypatch)
    monkeypatch.setattr(board.ollama_connector, "send_prompt_to_llm_sync", lambda *a, **k: "M")
    board.submit_prompt_to_bot(1, "advance")
    board.submit_prompt_to_bot(2, "advance")
    if after_turn:
        _complete_scheduled_turn(scheduled)
    pending = scheduled.pop(0)
    board.start_new_game()
    before = board.snapshot()
    pending(0)
    assert board.snapshot() == before
    assert board.history_manager.current_round is None
    assert board.current_turn == 0


@pytest.mark.parametrize("mode_key", ["prompt_augmentation", "independent_contexts"])
def test_ui_mode_changes_reset_history_before_building_header(monkeypatch, mode_key):
    config.set("game", "prompt_augmentation", True)
    config.set("game", "independent_contexts", True)
    connector = OllamaConnector()
    calls = []
    monkeypatch.setattr(connector.client, "chat", lambda **k: calls.append(deepcopy(k)) or {"message": {"content": "M"}})
    monkeypatch.setattr(connector, "_get_system_instructions_text",
                        lambda: f"modes:{connector.augmenting_prompt}:{connector.independent_contexts}")
    connector.send_prompt_to_llm_sync(1, user_text="old prompt", game_state={})
    config.set_temporary("game", mode_key, False)
    connector.send_prompt_to_llm_sync(1, user_text="new prompt", game_state={})
    assert calls[-1]["messages"][0]["content"] == (
        "modes:False:True" if mode_key == "prompt_augmentation" else "modes:True:False")
    assert not any("old prompt" in message["content"] for message in calls[-1]["messages"])
    if mode_key == "prompt_augmentation":
        assert calls[-1]["messages"][-1]["content"] == "new prompt"


def test_round_cancellation_cannot_restore_history_from_previous_context_mode(monkeypatch):
    board, scheduled, _ = _build_board(monkeypatch)
    board.ollama_connector._history_by_bot[1] = [{"role": "user", "content": "previous mode"}]
    config.set_temporary("game", "prompt_augmentation", False)
    board.submit_prompt_to_bot(1, "first")
    board.submit_prompt_to_bot(2, "second")
    board.cancel_current_round(board.get_bot_by_id(1), "cancelled")
    assert board.ollama_connector.augmenting_prompt is False
    assert board.ollama_connector._history_by_bot == {}
    assert board.ollama_connector._history_shared == []
    # The now-retired initial turn must also stay harmless after cancellation.
    scheduled.pop(0)(0)
    assert board.history_manager.current_round is None


@pytest.mark.parametrize("value", [None, 7, {}, "bad"])
def test_v3_malformed_prompt_containers_return_invalid_reports(value):
    payload = build()
    payload["games"][0]["rounds"][0]["prompts"] = value
    report = verify_payload(payload)
    assert not report.valid
    assert not report.schema_valid


@pytest.mark.parametrize("field", ["bot_id", "sequence", "attempts", "latency_ms"])
def test_v3_schema_rejects_boolean_numeric_fields(field):
    payload = build()
    payload["games"][0]["rounds"][0]["plays"][0][field] = True
    report = verify_payload(payload)
    assert not report.valid
    assert not report.schema_valid


@pytest.mark.parametrize("payload", [None, 7, [], "text"])
def test_v3_invalid_root_is_a_failed_report(payload):
    assert not verify_payload(payload).valid


def test_v3_verifier_preserves_mapping_interface():
    assert verify_payload(MappingProxyType(build())).valid


def test_invalid_utf8_is_reported_as_incompatible_input(tmp_path):
    path = tmp_path / "not-utf8.json"
    path.write_bytes(b"\xff")
    assert not verify_file(path).schema_valid
    with pytest.raises(SessionFormatError):
        load_session_payload(path)


@pytest.mark.parametrize("field,value", [
    ("bullet_damage", "nonsense"), ("bullet_damage", True), ("bullet_damage", 5.5),
    ("turns_per_round", 0), ("shield_initial_state", "false"), ("bot_step_length", "0.03"),
])
def test_v2_rejects_malformed_imported_rules(field, value):
    payload = _sample_payload()
    payload["games"][0]["rounds"][0]["gameplay_settings_snapshot"][field] = value
    with pytest.raises(SessionFormatError):
        validate_session_payload(payload)


def test_v2_rejects_missing_rule_while_configuration_can_use_defaults():
    payload = _sample_payload()
    del payload["games"][0]["rounds"][0]["gameplay_settings_snapshot"]["bullet_damage"]
    with pytest.raises(SessionFormatError, match="missing bullet_damage"):
        validate_session_payload(payload)
    assert GameplaySettingsSnapshot.from_mapping({}).bullet_damage == 5


def test_editor_reads_explicit_inventory_without_independent_discovery(editor, wire_server, monkeypatch):
    port, requests, _ = wire_server
    monkeypatch.setattr(service, "load_llm_config", lambda: pytest.fail("independent discovery"))
    assert editor.OllamaClient("http://127.0.0.1", port).list_local_models() == [{"name": "test:latest"}]
    assert requests == [("/api/tags", {})]


def test_editor_uses_strict_transport_with_its_real_deadline(editor, wire_server):
    port, requests, behaviour = wire_server
    client = editor.OllamaClient("http://127.0.0.1", port, timeout=0.03)
    behaviour["delay"] = 0.2
    with pytest.raises(ModelitoTimeoutError):
        client.run_once("test", "move")
    assert requests[0][1]["stream"] is False
    assert requests[0][1]["options"] == {"num_predict": 8}


def test_editor_management_keeps_explicit_endpoint_and_owned_shutdown(editor, monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(service, "_ownership_path", lambda _host: tmp_path / "no-owned-service")
    monkeypatch.setattr(service._MODELITO, "stop_service", lambda **k: pytest.fail("unsafe shutdown"))
    def sdk(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(delete=lambda name: calls.append(name),
                               generate=lambda **k: calls.append(k))
    monkeypatch.setattr(service, "_management_client", sdk)
    client = editor.OllamaClient("http://explicit", 12345)
    assert client.stop()["ok"]
    assert client.delete_model("test")["ok"]
    assert client.stop("test")["ok"]
    assert calls[0] == {"url": "http://explicit", "port": 12345}
    assert calls[2] == {"url": "http://explicit", "port": 12345}
    assert calls[-1]["keep_alive"] == 0


def test_editor_unload_and_delete_use_explicit_endpoint_at_wire_level(editor, wire_server, monkeypatch):
    port, requests, _behaviour = wire_server
    monkeypatch.setattr(service, "load_llm_config", lambda: pytest.fail("independent discovery"))
    client = editor.OllamaClient("http://127.0.0.1", port)
    assert client.stop("test")["ok"]
    assert client.delete_model("test")["ok"]
    assert requests[0][0] == "/api/generate"
    assert requests[0][1]["keep_alive"] == 0
    assert requests[0][1]["stream"] is False
    assert requests[1] == ("/api/delete", {"model": "test"})


def test_editor_delete_waits_for_confirmation_and_cancel_has_no_effect(editor, monkeypatch):
    actions, confirmations = [], []
    monkeypatch.setattr(editor, "show_confirmation_dialog", lambda *a, **k: confirmations.append(a[2]))
    monkeypatch.setattr(editor.threading, "Thread", lambda *, target, **k: SimpleNamespace(start=target))
    monkeypatch.setattr(editor.Clock, "schedule_once", lambda f, *a: f(0))
    panel = SimpleNamespace(spinner=SimpleNamespace(text="test"), output=SimpleNamespace(text=""),
                            refresh=lambda: None, delete_fn=lambda name: actions.append(name))
    editor.LocalModelsPanel.delete(panel)
    assert actions == []  # Leaving the confirmation unanswered/cancelling cannot delete.
    confirmations[0]()
    assert actions == ["test"]


def test_editor_model_unload_requires_confirmation(editor, monkeypatch):
    actions, confirmations = [], []
    monkeypatch.setattr(editor, "show_confirmation_dialog", lambda *a: confirmations.append(a[2]))
    monkeypatch.setattr(editor.threading, "Thread", lambda *, target, **k: SimpleNamespace(start=target))
    monkeypatch.setattr(editor.Clock, "schedule_once", lambda f, *a: f(0))
    panel = SimpleNamespace(spinner=SimpleNamespace(text="shared"), output=SimpleNamespace(text=""),
                            stop_fn=lambda name: actions.append(name))
    editor.LocalModelsPanel.stop(panel)
    assert actions == []
    confirmations[0]()
    assert actions == ["shared"]


def test_editor_console_cancel_never_stops_models_or_service(editor):
    panel = SimpleNamespace(_stop_flag=False,
                            app_ref=SimpleNamespace(_stop_models=lambda *a: pytest.fail("service mutation")))
    editor.ConsolePanel.stop(panel)
    assert panel._stop_flag


def test_console_cancellation_closes_iterator_and_retires_pending_output(editor, monkeypatch):
    closed, callbacks, output = [], [], []
    panel = SimpleNamespace(_gen_thread=None, _stop_flag=False,
                            model_spinner=SimpleNamespace(text="test"),
                            prompt=SimpleNamespace(text="prompt"), output=SimpleNamespace(text=""),
                            _append=output.append)
    def stream(*_args):
        try:
            yield "queued before stop"
            editor.ConsolePanel.stop(panel)
            yield "arrived after stop"
        finally:
            closed.append(True)
    panel.app_ref = SimpleNamespace(ollama=SimpleNamespace(stream_generate=stream))
    monkeypatch.setattr(editor.threading, "Thread", lambda *, target, **k: SimpleNamespace(start=target))
    monkeypatch.setattr(editor.Clock, "schedule_once", lambda f, *a: callbacks.append(f))
    editor.ConsolePanel.generate(panel)
    panel._stop_flag = False  # A later request must not revive cancelled callbacks.
    for callback in callbacks:
        callback(0)
    assert output == []
    assert closed == [True]


def test_editor_streaming_uses_same_explicit_native_transport(editor, wire_server):
    port, requests, _behaviour = wire_server
    assert list(editor.OllamaClient("http://127.0.0.1", port, timeout=0.5)
                .stream_generate("test", "move", num_predict=12)) == ["M"]
    assert requests[0][1]["stream"] is True
    assert requests[0][1]["options"]["num_predict"] == 12


def test_editor_manual_download_waits_for_confirmation(editor, monkeypatch):
    actions, confirmations = [], []
    monkeypatch.setattr(editor, "show_confirmation_dialog", lambda *a: confirmations.append(a[2]))
    monkeypatch.setattr(editor.threading, "Thread", lambda *, target, **k: SimpleNamespace(start=target))
    monkeypatch.setattr(editor.Clock, "schedule_once", lambda f, *a: f(0))
    panel = SimpleNamespace(model_name=SimpleNamespace(text="registry/model:tag"),
                            spinner=SimpleNamespace(text="(refresh)"), output=SimpleNamespace(text=""),
                            pull_fn=lambda name, **k: actions.append(name), _append=lambda _s: None)
    editor.RemoteModelsPanel.pull(panel)
    assert actions == []
    confirmations[0]()
    assert actions == ["registry/model:tag"]


def test_selection_does_not_unload_a_persisted_model(monkeypatch):
    config.set("llm", "last_served_model", "external-now")
    screen = OllamaConfigScreen()
    assert screen._managed_model_name is None
    monkeypatch.setattr(screen, "_run_in_thread", lambda fn: fn())
    monkeypatch.setattr("view.ollama_config_screen.Clock.schedule_once", lambda f, *a: f(0))
    monkeypatch.setattr(screen, "_ensure_model_serving", lambda _n: None)
    monkeypatch.setattr(screen, "_stop_serving_model", lambda _n: pytest.fail("implicit unload"))
    monkeypatch.setattr(screen, "refresh_local_models", lambda: None)
    monkeypatch.setattr(screen, "refresh_ollama_status", lambda: None)
    screen.selected_local_model = "new"
    screen.set_model_from_selection()
    assert config.get("llm", "model") == "new"


def test_stale_selection_completion_cannot_overwrite_latest_choice(monkeypatch):
    workers, completions = [], []
    screen = OllamaConfigScreen()
    monkeypatch.setattr(screen, "_run_in_thread", workers.append)
    monkeypatch.setattr("view.ollama_config_screen.Clock.schedule_once", lambda f, *a: completions.append(f))
    monkeypatch.setattr(screen, "_set_status", lambda _s: None)
    monkeypatch.setattr(screen, "_append_log", lambda _s: None)
    monkeypatch.setattr(screen, "_ensure_model_serving", lambda _n: None)
    monkeypatch.setattr(screen, "refresh_local_models", lambda: None)
    monkeypatch.setattr(screen, "refresh_ollama_status", lambda: None)
    screen.selected_local_model = "older"
    screen.set_model_from_selection()
    workers[0]()  # Warm-up completed; its UI commit remains queued.
    screen.selected_local_model = "newer"
    screen.set_model_from_selection()
    workers[1]()
    completions[1](0)
    completions[0](0)
    assert config.get("llm", "model") == "newer"
    assert AppConfig(path=config._path).get("llm", "model") == "newer"


def test_missing_startup_model_reports_failure_without_pulling(monkeypatch):
    commands = []
    monkeypatch.setattr(service, "load_llm_config", lambda _p: {"model": "missing", "url": "http://test", "port": 123})
    monkeypatch.setattr(service, "server_is_up", lambda *a: True)
    monkeypatch.setattr(service, "run_ollama_command", lambda *a, **k: commands.append(a) or SimpleNamespace(returncode=0, stdout="ok", stderr=""))
    monkeypatch.setattr(service, "preload_model", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("HTTP 404")))
    monkeypatch.setattr(service, "save_last_served_model", lambda *a: pytest.fail("model was not ready"))
    assert service.start_service() == 1
    assert commands == [("--version",)]


def test_catalogue_unavailability_is_explicit_and_manual_entry_does_not_download(monkeypatch):
    def fail_catalogue(**kwargs):
        raise RuntimeError("catalogue offline")
    monkeypatch.setattr(service._MODELITO, "list_remote_model_catalog", fail_catalogue)
    with pytest.raises(service.RemoteCatalogueUnavailable, match="Enter a model name"):
        service.list_remote_model_catalog()
    screen = OllamaConfigScreen()
    monkeypatch.setattr("view.ollama_config_screen.show_text_input_dialog",
                        lambda **k: k["on_confirm"]("registry/model:tag"))
    monkeypatch.setattr(screen, "_pull_model", lambda _n: pytest.fail("download without confirmation"))
    screen.enter_remote_model_name()
    assert screen.selected_remote_model == "registry/model:tag"


def test_empty_remote_selector_attempts_discovery_before_manual_recovery(monkeypatch):
    screen = OllamaConfigScreen()
    opened = []
    monkeypatch.setattr(screen, "enter_remote_model_name", lambda: opened.append(True))
    refreshed = []
    def refresh(**kwargs):
        refreshed.append(True)
        kwargs["on_complete"]()
    monkeypatch.setattr(screen, "refresh_remote_models", refresh)
    screen.open_remote_model_selector()
    assert opened == [True]
    assert refreshed == [True]


def test_extracted_research_package_generates_and_verifies_without_checkout(tmp_path, monkeypatch):
    spec = import_util.spec_from_file_location("research_package", ROOT / "research/urucon2026/build_artifact.py")
    package = import_util.module_from_spec(spec)
    spec.loader.exec_module(package)
    files = package.selected_files()
    source = tmp_path / "source"
    for path in files:
        target = source / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    monkeypatch.setattr(package, "ROOT", source)
    monkeypatch.setattr(package, "CORE_PATHS", [source / p.relative_to(ROOT) for p in files])
    output = source / "research/urucon2026/artifact"
    monkeypatch.setattr(package, "ARTIFACT", output)
    monkeypatch.setattr(package, "PACKAGE", output / "research.zip")
    monkeypatch.setattr(package, "MANIFEST", output / "MANIFEST.sha256")
    monkeypatch.setattr(package, "PACKAGE_HASH", output / "PACKAGE.sha256")
    assert package.main() == 0
    extracted = tmp_path / "extracted"
    with zipfile.ZipFile(package.PACKAGE) as archive:
        archive.extractall(extracted)
    assert (extracted / "VERSION").read_bytes() == (ROOT / "VERSION").read_bytes()
    env = {**os.environ, "PYTHONPATH": str(extracted / "src"), "BATLLM_HOME": str(tmp_path / "state")}
    trace, report = tmp_path / "trace.json", tmp_path / "report.json"
    for arguments in (
        ["run_batllm_research.py", "--provider", "scripted", "--turns", "2", "--output", str(trace)],
        ["run_batllm_verify.py", str(trace), "--json", str(report)],
    ):
        result = subprocess.run([sys.executable, *arguments], cwd=extracted, env=env,
                                capture_output=True, text=True, timeout=30, check=False)
        assert result.returncode == 0, result.stderr
    assert json.loads(report.read_text())["valid"] is True


def test_catalogue_uses_configured_endpoint_and_preserves_ui_entry_shape(monkeypatch):
    from types import SimpleNamespace
    entries = [SimpleNamespace(name="foo", installed=True)]
    calls = []
    monkeypatch.setattr(service, "load_llm_config",
                        lambda: {"url": "http://localhost", "port": 12345})
    def catalogue(**kwargs):
        calls.append(kwargs)
        return entries
    monkeypatch.setattr(service._MODELITO, "list_remote_model_catalog", catalogue)
    assert service.list_remote_model_catalog() == entries
    assert calls == [{"host": "http://localhost", "port": 12345, "timeout": 30.0}]
    screen = OllamaConfigScreen()
    assert screen._list_remote_model_catalog_via_modelito() == [
        {"name": "foo", "display": "foo (installed)", "size": ""}]


def test_remote_selector_shows_discovered_models(monkeypatch):
    screen = OllamaConfigScreen()
    opened = []
    def refresh(**kwargs):
        screen._remote_model_entries = [{"name": "foo", "display": "foo"}]
        screen.remote_models = ["foo"]
        kwargs["on_complete"]()
    monkeypatch.setattr(screen, "refresh_remote_models", refresh)
    monkeypatch.setattr(screen, "enter_remote_model_name", lambda: pytest.fail("discovery succeeded"))
    monkeypatch.setattr(screen, "_show_model_picker", lambda **kwargs: opened.append(kwargs))
    screen.open_remote_model_selector()
    assert opened[0]["entries"] == [{"name": "foo", "display": "foo"}]


def test_editor_catalogue_uses_edited_endpoint(editor, monkeypatch):
    calls = []
    monkeypatch.setattr(service, "list_remote_model_catalog",
                        lambda **kwargs: calls.append(kwargs) or [])
    app = SimpleNamespace(ollama=editor.OllamaClient("http://localhost", 12345))
    assert editor.BatLLMConfigApp._remote_models(app) == []
    assert calls == [{"url": "http://localhost", "port": 12345}]
