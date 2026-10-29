"""Regressions for transport provenance, unsafe input and service ownership."""
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import time
from types import SimpleNamespace

import pytest

from analyzer_model import AnalyzerSessionModel
from configs.app_config import AppConfig
from game.research_runtime import ModelitoChatClient
from game.session_schema import SessionFormatError, validate_session_payload
from llm.chat import Client
from llm import service
from modelito.exceptions import LLMProviderError, ModelitoTimeoutError
from tests.test_game_analyzer import _sample_payload


@pytest.fixture
def wire_server():
    requests = []
    behaviour = {"status": 200, "body": {"message": {"content": "M"}, "done": True}}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_GET(self):
            requests.append((self.path, {}))
            data = json.dumps({"models": [{"name": "test:latest"}]}).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_DELETE(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append((self.path, payload))
            data = b'{"status":"success"}'
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append((self.path, payload))
            time.sleep(behaviour.get("delay", 0))
            body = behaviour["body"]
            if isinstance(body, dict):
                body = json.dumps({"model": payload["model"], **body})
            data = body.encode("utf-8")
            self.send_response(behaviour["status"])
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    yield server.server_port, requests, behaviour
    server.shutdown()
    server.server_close()
    worker.join(timeout=2)


@pytest.mark.parametrize("research", [False, True])
def test_both_runtimes_send_native_chat_roles_options_and_deadlines(wire_server, research):
    port, requests, _behaviour = wire_server
    client = (ModelitoChatClient(host="http://127.0.0.1", port=port) if research
              else Client(host=f"http://127.0.0.1:{port}"))
    messages = [{"role": "system", "content": "système"},
                {"role": "user", "content": "move"},
                {"role": "assistant", "content": "S1"},
                {"role": "user", "content": "again"}]
    options = {"temperature": 0.2, "seed": 42, "num_ctx": 2048,
               "num_predict": 30, "timeout": 0.5}
    response = client.chat(model="test-model", messages=messages, options=options)
    assert (response if research else response["message"]["content"]) == "M"
    assert requests == [("/api/chat", {"model": "test-model", "messages": messages,
                        "stream": False, "options": {k: v for k, v in options.items() if k != "timeout"}})]


@pytest.mark.parametrize("body,status", [
    ({"error": "missing model"}, 404),
    ({"error": "inference failed"}, 200),
    ("not json", 200),
    ('{"message":{"content":"M"}}\n{"done":true}\n', 200),
    ({"message": {"content": 42}}, 200),
    ({"message": {"content": ""}}, 200),
])
def test_failed_inference_never_returns_prompt_or_cli_output(wire_server, monkeypatch, body, status):
    port, requests, behaviour = wire_server
    behaviour.update(body=body, status=status)
    monkeypatch.setattr("modelito.ollama.run_ollama_command",
                        lambda *a, **k: pytest.fail("Inference must never use CLI"))
    with pytest.raises((LLMProviderError, ValueError)):
        Client(f"http://127.0.0.1:{port}").chat(
            model="missing", messages=[{"role": "user", "content": "M"}])
    assert len(requests) == 1


def test_timeout_setting_reaches_actual_transport(wire_server):
    port, _requests, behaviour = wire_server
    behaviour["delay"] = 0.2
    with pytest.raises(ModelitoTimeoutError):
        Client(f"http://127.0.0.1:{port}").chat(
            model="test", messages=[{"role": "user", "content": "M"}],
            options={"timeout": 0.03})


def test_inventory_reads_explicit_endpoint(wire_server, monkeypatch):
    port, requests, _behaviour = wire_server
    monkeypatch.setattr(service, "load_llm_config",
                        lambda: {"url": "http://127.0.0.1", "port": port})
    assert service.list_local_models() == ["test:latest"]
    assert requests == [("/api/tags", {})]


def test_unavailable_server_is_an_error(wire_server):
    port, _requests, _behaviour = wire_server
    # Closing only this test-owned server cannot affect a real Ollama instance.
    # Use a non-listening ephemeral port after an isolated socket is closed.
    import socket
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    with pytest.raises(LLMProviderError):
        Client(f"http://127.0.0.1:{port}", timeout=0.1).chat(
            model="test", messages=[{"role": "user", "content": "M"}])


@pytest.mark.parametrize("play", [None, 5, [], {}, {"bot_id": True},
    {"bot_id": 99, "cmd": "M", "llm_response": "M"},
    {"bot_id": 1, "cmd": "M", "llm_response": []}])
def test_malformed_v2_plays_are_rejected(play):
    payload = _sample_payload()
    payload["games"][0]["rounds"][0]["turns"][0]["plays"] = [play]
    with pytest.raises(SessionFormatError):
        validate_session_payload(payload)


def test_v2_analyser_flags_response_disagreement_and_turn_discontinuity():
    payload = _sample_payload()
    round_entry = payload["games"][0]["rounds"][0]
    turn = round_entry["turns"][0]
    turn["plays"][0]["llm_response"] = "M"
    following = deepcopy(turn)
    following["pre_state"]["1"]["health"] -= 1
    round_entry["turns"].append(following)
    model = AnalyzerSessionModel(payload, "test.json")
    details = [d for step in model.round_steps() for d in step["turn_replay"].mismatch_details]
    assert any("response-command" in detail for detail in details)
    assert any("continuity" in detail for detail in details)


@pytest.mark.parametrize("yaml_text", ["[]", "llm: []", "game: text", "ui: null"])
def test_non_mapping_yaml_is_rejected_with_clear_error(tmp_path, yaml_text):
    path = tmp_path / "config.yaml"
    path.write_text(yaml_text)
    with pytest.raises(ValueError, match="mapping"):
        AppConfig(path=path)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1, 0])
def test_non_finite_timeouts_do_not_become_request_deadlines(value):
    assert service._parse_positive_timeout(value) is None


@pytest.mark.parametrize("reused", [False, True])
def test_shutdown_requires_owned_pid_birth_time_and_command(monkeypatch, tmp_path, reused):
    monkeypatch.setattr(service, "load_llm_config", lambda _p: {"url": "http://local", "port": 123})
    path = tmp_path / "ownership.json"
    monkeypatch.setattr(service, "_ownership_path", lambda _h: path)
    path.write_text(json.dumps({"host": "local:123", "pid": 4321, "created": 100.0}))
    terminated = []
    process = SimpleNamespace(create_time=lambda: 200.0 if reused else 100.0,
                              name=lambda: "ollama", cmdline=lambda: ["ollama", "serve"],
                              terminate=lambda: terminated.append(True), wait=lambda **k: None)
    monkeypatch.setattr(service.psutil, "Process", lambda _pid: process)
    assert service.stop_service() == (1 if reused else 0)
    assert terminated == ([] if reused else [True])


def test_session_saving_does_not_fetch_live_metadata(monkeypatch):
    monkeypatch.setattr(service, "lookup_model_metadata", lambda *a, **k: pytest.fail("network I/O"))
    assert service.build_saved_llm_metadata_snapshot()["provider_metadata"] == {}


def test_provider_timeouts_retry_then_recover_without_failed_prompt(monkeypatch):
    from game.ollama_connector import OllamaConnector, LLMTimeoutError
    connector = OllamaConnector()
    monkeypatch.setattr(connector, "load_options", lambda: None)
    calls = []

    def chat(**kwargs):
        calls.append(deepcopy(kwargs["messages"]))
        if len(calls) < 3:
            raise ModelitoTimeoutError("timed out")
        return {"message": {"content": "M"}}

    connector.client = SimpleNamespace(chat=chat)
    with pytest.raises(LLMTimeoutError) as error:
        connector.send_prompt_to_llm_sync(1, user_text="failed", game_state={})
    assert error.value.attempts == 2
    assert calls[0] == calls[1]
    assert connector.send_prompt_to_llm_sync(1, user_text="recovery", game_state={}) == "M"
    assert not any("failed" in m["content"] for m in calls[2])


@pytest.mark.parametrize("method,field", [
    ("save_selected_model_timeout", "selected_local_timeout_text"),
    ("save_warmup_timeout", "warmup_timeout_text"),
])
@pytest.mark.parametrize("value", ["nan", "inf"])
def test_timeout_editors_refuse_non_finite_values(monkeypatch, method, field, value):
    from configs.app_config import config
    from view.ollama_config_screen import OllamaConfigScreen
    screen = OllamaConfigScreen()
    screen.selected_local_model = "test-model"
    setattr(screen, field, value)
    before = deepcopy(config.as_dict())
    getattr(screen, method)()
    assert config.as_dict() == before


def test_failed_model_readiness_preserves_saved_selection(monkeypatch, tmp_path):
    from configs.app_config import config
    from view.ollama_config_screen import OllamaConfigScreen
    config.set("llm", "model", "previous")
    config.save()
    screen = OllamaConfigScreen()
    screen.selected_local_model = "unready"
    monkeypatch.setattr(screen, "_run_in_thread", lambda fn: fn())
    monkeypatch.setattr(screen, "_get_running_model_names", lambda: [])
    monkeypatch.setattr(screen, "_ensure_model_serving", lambda _m: (_ for _ in ()).throw(RuntimeError("failed")))
    screen.set_model_from_selection()
    assert config.get("llm", "model") == "previous"
    assert AppConfig(path=config._path).get("llm", "model") == "previous"


def test_untrusted_analyser_text_is_escaped():
    payload = _sample_payload()
    payload["games"][0]["rounds"][0]["prompts"][0]["prompt"] = "[ref=attack]prompt[/ref]"
    payload["llm_metadata"] = {"configured_model": "[b]fake[/b]"}
    model = AnalyzerSessionModel(payload, "test.json")
    assert "[ref=attack]" not in model.format_prompts()
    assert "&bl;ref=attack&br;" in model.format_prompts()
    assert "[b]fake[/b]" not in model.format_model_metadata()


def test_legacy_sessions_are_copied_without_overwriting_user_state(monkeypatch, tmp_path):
    from util import paths
    legacy = tmp_path / "repo" / "saves"
    target = tmp_path / "home" / "saves"
    legacy.mkdir(parents=True)
    target.mkdir(parents=True)
    (legacy / "old.json").write_text('{"legacy":true}')
    (legacy / "same.json").write_text("legacy")
    (target / "same.json").write_text("user")
    monkeypatch.setattr(paths, "ROOT_DIR", legacy.parent)
    monkeypatch.setattr(paths, "configured_batllm_home", lambda: None)
    monkeypatch.setattr(paths, "default_batllm_home", lambda: target.parent)
    assert paths.resolve_saved_sessions_dir("saves") == target
    assert (target / "old.json").read_bytes() == (legacy / "old.json").read_bytes()
    assert (target / "same.json").read_text() == "user"
    assert (legacy / "old.json").exists()
    assert not list(target.glob(".legacy-session-*"))


def test_platform_bundle_excludes_research_and_development_files(monkeypatch, tmp_path):
    import create_release_bundles as bundles
    root = tmp_path / "repo"
    relative_paths = ["src/main.py", "src/tests/test_private.py", "requirements.txt",
                      "research/corpus/large.json", "docs/screenshots/large.png",
                      "research/urucon2026/schema/batllm-session-v3.schema.json"]
    files = []
    for relative in relative_paths:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("test")
        files.append(path)
    monkeypatch.setattr(bundles, "ROOT", root)
    monkeypatch.setattr(bundles, "tracked_files", lambda: files)
    monkeypatch.setattr(bundles.tempfile, "mkdtemp", lambda **k: str(tmp_path / "stage"))
    stage = bundles.stage_release("runtime", {"launcher.sh": "test"})
    assert (stage / "src/main.py").exists()
    assert (stage / "requirements.txt").exists()
    assert not (stage / "src/tests").exists()
    assert (stage / "src/assets/batllm-session-v3.schema.json").exists()
    assert not (stage / "research").exists()
    assert not (stage / "docs").exists()
