from __future__ import annotations

import py_compile
from pathlib import Path
from types import SimpleNamespace

import ollama_service
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
        "model": "qwen3:latest",
        "url": "http://localhost",
        "port": 11434,
    }


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


def test_cross_platform_launchers_compile() -> None:
    root = Path(__file__).resolve().parents[2]

    for script in (
        root / "run_batllm.py",
        root / "run_tests.py",
        root / "create_release_bundles.py",
    ):
        py_compile.compile(str(script), doraise=True)
