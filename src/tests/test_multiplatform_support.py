from __future__ import annotations

import py_compile
from pathlib import Path
from types import SimpleNamespace

from configs.app_config import DEFAULTS
from llm import service as ollama_service
import yaml
from util import paths


def test_resolve_repo_relative_finds_system_instruction_file() -> None:
    resolved = paths.resolve_repo_relative(
        "src/assets/system_instructions/augmented_independent_1.txt"
    )

    assert resolved.is_absolute()
    assert resolved.exists()
    assert resolved.name == "augmented_independent_1.txt"


def test_prompt_asset_dir_is_absolute_and_exists() -> None:
    prompt_dir = paths.prompt_asset_dir()

    assert prompt_dir.is_absolute()
    assert prompt_dir.exists()
    assert prompt_dir.name == "prompts"


def test_load_llm_config_reads_yaml_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "llm:\n  model: qwen3:latest\n  url: http://localhost\n  port: 11434\n",
        encoding="utf-8",
    )

    loaded = ollama_service.load_llm_config(config_path)

    assert loaded == {
        "last_served_model": "",
        "model": "qwen3:latest",
        "model_timeouts": {},
        "timeout": None,
        "url": "http://localhost",
        "port": 11434,
    }


def test_resolve_request_timeout_uses_configured_value() -> None:
    assert ollama_service.resolve_request_timeout({"timeout": 75}) == 75.0
    assert ollama_service.resolve_request_timeout({"timeout": "90"}) == 90.0


def test_resolve_request_timeout_prefers_model_override() -> None:
    assert ollama_service.resolve_request_timeout(
        {
            "model": "qwen3:30b",
            "model_timeouts": {"qwen3:30b": "180"},
            "timeout": 75,
        },
        model="qwen3:30b",
    ) == 180.0


def test_resolve_request_timeout_uses_common_model_default() -> None:
    assert ollama_service.resolve_request_timeout(
        {
            "model": "llama3.2:latest",
            "model_timeouts": {},
            "timeout": None,
        },
        model="llama3.2:latest",
    ) == 75.0


def test_load_remote_timeout_catalog_contains_family_rules() -> None:
    catalog = ollama_service.load_remote_timeout_catalog()

    assert catalog["default_timeout"] == 120.0
    assert catalog["family_overrides"]
    assert catalog["size_bands"]


def test_estimate_remote_model_timeout_uses_family_rule() -> None:
    timeout, source = ollama_service.estimate_remote_model_timeout_details(
        "qwen3", size_label="30b")

    assert timeout == 120.0
    assert "Qwen 3 family rule" in source


def test_estimate_remote_model_timeout_uses_keyword_adjustment() -> None:
    timeout, source = ollama_service.estimate_remote_model_timeout_details(
        "llava-phi3",
        size_label="3.8b",
    )

    assert timeout == 90.0
    assert "multimodal-model adjustment" in source


def test_estimate_remote_model_timeout_falls_back_to_size_band() -> None:
    timeout, source = ollama_service.estimate_remote_model_timeout_details(
        "llama3.1",
        size_label="8b",
    )

    assert timeout == 80.0
    assert "8B remote size band" in source


def test_resolve_request_timeout_falls_back_to_default() -> None:
    assert ollama_service.resolve_request_timeout({"timeout": None}) == 120.0
    assert ollama_service.resolve_request_timeout({"timeout": 0}) == 120.0
    assert ollama_service.resolve_request_timeout({"timeout": "invalid"}) == 120.0


def test_preferred_start_model_prefers_last_served_model() -> None:
    llm = {
        "last_served_model": "mistral-small:latest",
        "model": "qwen3:latest",
        "url": "http://localhost",
        "port": 11434,
    }

    assert ollama_service.preferred_start_model(llm) == "mistral-small:latest"


def test_preferred_start_model_falls_back_to_configured_model() -> None:
    llm = {
        "last_served_model": "",
        "model": "smollm2",
        "url": "http://localhost",
        "port": 11434,
    }

    assert ollama_service.preferred_start_model(llm) == "smollm2"


def test_save_last_served_model_updates_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "llm:\n  model: qwen3:latest\n  url: http://localhost\n  port: 11434\n",
        encoding="utf-8",
    )

    ollama_service.save_last_served_model("mistral-small:latest", config_path)

    saved = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

    assert saved["llm"]["last_served_model"] == "mistral-small:latest"


def test_find_ollama_listener_pids_filters_by_listen_port(monkeypatch) -> None:
    connections = [
        SimpleNamespace(
            status=ollama_service.psutil.CONN_LISTEN,
            laddr=SimpleNamespace(port=11434),
            pid=101,
        ),
        SimpleNamespace(
            status=ollama_service.psutil.CONN_LISTEN,
            laddr=SimpleNamespace(port=9999),
            pid=202,
        ),
        SimpleNamespace(
            status="ESTABLISHED",
            laddr=SimpleNamespace(port=11434),
            pid=303,
        ),
    ]

    monkeypatch.setattr(ollama_service.psutil, "net_connections", lambda kind="inet": connections)

    assert ollama_service.find_ollama_listener_pids(11434) == [101]


def test_find_ollama_listener_pids_falls_back_when_net_connections_denied(monkeypatch) -> None:
    class FakeProcess:
        def __init__(self, pid: int, name: str, connections):
            self.pid = pid
            self.info = {"pid": pid, "name": name}
            self._connections = connections

        def name(self):
            return self.info["name"]

        def net_connections(self, kind="inet"):
            _ = kind
            return self._connections

    monkeypatch.setattr(
        ollama_service.psutil,
        "net_connections",
        lambda kind="inet": (_ for _ in ()).throw(ollama_service.psutil.AccessDenied()),
    )
    monkeypatch.setattr(
        ollama_service.psutil,
        "process_iter",
        lambda _attrs=None: [
            FakeProcess(
                101,
                "ollama",
                [
                    SimpleNamespace(
                        status=ollama_service.psutil.CONN_LISTEN,
                        laddr=SimpleNamespace(port=11434),
                        pid=None,
                    )
                ],
            ),
            FakeProcess(
                202,
                "python",
                [
                    SimpleNamespace(
                        status=ollama_service.psutil.CONN_LISTEN,
                        laddr=SimpleNamespace(port=11434),
                        pid=202,
                    )
                ],
            ),
        ],
    )

    assert ollama_service.find_ollama_listener_pids(11434) == [101]


def test_install_command_for_current_platform_is_platform_specific() -> None:
    assert ollama_service.install_command_for_current_platform("linux") == (
        ["/bin/sh", "-lc", "export OLLAMA_NO_START=1; curl -fsSL https://ollama.com/install.sh | sh"],
        "export OLLAMA_NO_START=1; curl -fsSL https://ollama.com/install.sh | sh",
    )
    assert ollama_service.install_command_for_current_platform("darwin") == (
        ["/bin/sh", "-lc", "export OLLAMA_NO_START=1; curl -fsSL https://ollama.com/install.sh | sh"],
        "export OLLAMA_NO_START=1; curl -fsSL https://ollama.com/install.sh | sh",
    )
    assert ollama_service.install_command_for_current_platform("win32") == (
        [
            "powershell.exe",
            "-NoExit",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "irm https://ollama.com/install.ps1 | iex",
        ],
        "irm https://ollama.com/install.ps1 | iex",
    )


def test_start_service_uses_last_served_model_and_persists_it(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        (
            "llm:\n"
            "  model: qwen3:latest\n"
            "  last_served_model: mistral-small:latest\n"
            "  timeout: 180\n"
            "  url: http://localhost\n"
            "  port: 11434\n"
        ),
        encoding="utf-8",
    )

    saved = {}
    commands = []
    preload = {}

    def fake_run_ollama_command(*args: str, host: str | None = None):
        commands.append((args, host))
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(ollama_service, "run_ollama_command", fake_run_ollama_command)
    monkeypatch.setattr(ollama_service, "server_is_up", lambda _url, _port: False)
    monkeypatch.setattr(ollama_service, "start_detached_ollama_serve", lambda _host: None)
    monkeypatch.setattr(ollama_service, "wait_until_ready", lambda _url, _port: None)
    monkeypatch.setattr(
        ollama_service,
        "preload_model",
        lambda _url, _port, _model, timeout=120.0: preload.update(
            {"timeout": timeout, "model": _model}),
    )
    monkeypatch.setattr(
        ollama_service,
        "save_last_served_model",
        lambda model, path=ollama_service.CONFIG_PATH: saved.update({"model": model, "path": path}),
    )

    assert ollama_service.start_service(config_path) == 0
    assert saved == {"model": "mistral-small:latest", "path": config_path}
    assert preload == {"timeout": 180.0, "model": "mistral-small:latest"}
    assert commands[1][0] == ("pull", "mistral-small:latest")


def test_start_service_uses_model_specific_timeout_override(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        (
            "llm:\n"
            "  model: qwen3:30b\n"
            "  last_served_model: qwen3:30b\n"
            "  timeout: 60\n"
            "  model_timeouts:\n"
            "    qwen3:30b: 180\n"
            "  url: http://localhost\n"
            "  port: 11434\n"
        ),
        encoding="utf-8",
    )

    preload = {}

    monkeypatch.setattr(
        ollama_service,
        "run_ollama_command",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="ok", stderr=""),
    )
    monkeypatch.setattr(ollama_service, "server_is_up", lambda _url, _port: False)
    monkeypatch.setattr(ollama_service, "start_detached_ollama_serve", lambda _host: None)
    monkeypatch.setattr(ollama_service, "wait_until_ready", lambda _url, _port: None)
    monkeypatch.setattr(
        ollama_service,
        "preload_model",
        lambda _url, _port, _model, timeout=120.0: preload.update(
            {"timeout": timeout, "model": _model}
        ),
    )
    monkeypatch.setattr(ollama_service, "save_last_served_model", lambda *_args, **_kwargs: None)

    assert ollama_service.start_service(config_path) == 0
    assert preload == {"timeout": 180.0, "model": "qwen3:30b"}


def test_start_service_uses_configured_model_for_fresh_install(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        (
            "llm:\n"
            "  model: smollm2\n"
            "  last_served_model: ''\n"
            "  timeout: null\n"
            "  url: http://localhost\n"
            "  port: 11434\n"
        ),
        encoding="utf-8",
    )

    saved = {}
    commands = []
    preload = {}

    def fake_run_ollama_command(*args: str, host: str | None = None):
        commands.append((args, host))
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(ollama_service, "run_ollama_command", fake_run_ollama_command)
    monkeypatch.setattr(ollama_service, "server_is_up", lambda _url, _port: False)
    monkeypatch.setattr(ollama_service, "start_detached_ollama_serve", lambda _host: None)
    monkeypatch.setattr(ollama_service, "wait_until_ready", lambda _url, _port: None)
    monkeypatch.setattr(
        ollama_service,
        "preload_model",
        lambda _url, _port, _model, timeout=120.0: preload.update(
            {"timeout": timeout, "model": _model}
        ),
    )
    monkeypatch.setattr(
        ollama_service,
        "save_last_served_model",
        lambda model, path=ollama_service.CONFIG_PATH: saved.update({"model": model, "path": path}),
    )

    assert ollama_service.start_service(config_path) == 0
    assert saved == {"model": "smollm2", "path": config_path}
    assert preload == {"timeout": 35.0, "model": "smollm2"}
    assert commands[1][0] == ("pull", "smollm2")


def test_cross_platform_launchers_compile() -> None:
    root = Path(__file__).resolve().parents[2]

    for script in (
        root / "run_batllm.py",
        root / "run_game_analyzer.py",
        root / "run_tests.py",
        root / "create_release_bundles.py",
        root / "create_homebrew_formula.py",
    ):
        py_compile.compile(str(script), doraise=True)


def test_release_bundle_wrappers_include_game_analyzer_launchers() -> None:
    from create_release_bundles import (
        linux_wrapper_contents,
        macos_wrapper_contents,
        windows_wrapper_contents,
    )

    assert "run-game-analyzer.bat" in windows_wrapper_contents("0.2.3")
    assert "run-game-analyzer.command" in macos_wrapper_contents("0.2.3")
    assert "run-game-analyzer.sh" in linux_wrapper_contents("0.2.3")


def test_app_config_defaults_match_shipped_config_for_fallback_keys() -> None:
    config_path = Path(__file__).resolve().parents[1] / "configs" / "config.yaml"
    shipped = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

    for section in ("game", "ui", "llm"):
        values = DEFAULTS[section]
        for key, value in values.items():
            assert shipped[section][key] == value
