from __future__ import annotations

import tarfile
from pathlib import Path

import yaml

import ollama_service
from configs.app_config import AppConfig
from create_homebrew_formula import (
    create_worktree_archive,
    parse_downloaded_artifact_name,
    read_requirements,
    render_formula,
)
from util import paths


ROOT = Path(__file__).resolve().parents[2]
HOMEBREW_REQUIREMENTS = ROOT / "packaging" / "homebrew" / "requirements.txt"


def test_batllm_home_redirects_relative_saved_session_paths(monkeypatch, tmp_path: Path) -> None:
    runtime_home = tmp_path / "batllm-home"
    monkeypatch.setenv(paths.BATLLM_HOME_ENV, str(runtime_home))

    resolved = paths.resolve_saved_sessions_dir("saved_sessions")

    assert resolved == runtime_home / "saved_sessions"
    assert resolved.exists()


def test_app_config_uses_shipped_defaults_before_runtime_overlay(tmp_path: Path) -> None:
    shipped_path = tmp_path / "shipped-config.yaml"
    shipped_path.write_text(
        (
            "llm:\n"
            "  model: smollm2\n"
            "  last_served_model: ''\n"
            "  url: http://localhost\n"
            "  port: 11434\n"
            "ui:\n"
            "  confirm_on_exit: true\n"
        ),
        encoding="utf-8",
    )
    runtime_path = tmp_path / "runtime-home" / "config.yaml"
    runtime_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_path.write_text("llm:\n  last_served_model: mistral-small:latest\n", encoding="utf-8")

    config = AppConfig(path=runtime_path, default_path=shipped_path)

    assert config.get("llm", "model") == "smollm2"
    assert config.get("llm", "last_served_model") == "mistral-small:latest"

    config.set("ui", "confirm_on_exit", False)
    config.save()

    saved = yaml.safe_load(runtime_path.read_text(encoding="utf-8")) or {}
    assert saved["llm"]["model"] == "smollm2"
    assert saved["ui"]["confirm_on_exit"] is False


def test_load_llm_config_falls_back_to_shipped_config_when_runtime_file_is_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    shipped_path = tmp_path / "shipped-config.yaml"
    shipped_path.write_text(
        (
            "llm:\n"
            "  model: smollm2\n"
            "  last_served_model: ''\n"
            "  url: http://localhost\n"
            "  port: 11434\n"
        ),
        encoding="utf-8",
    )
    runtime_path = tmp_path / "runtime-home" / "config.yaml"

    monkeypatch.setattr(ollama_service, "SHIPPED_CONFIG_PATH", shipped_path)

    loaded = ollama_service.load_llm_config(runtime_path)

    assert loaded["model"] == "smollm2"
    assert loaded["last_served_model"] == ""
    assert loaded["port"] == 11434


def test_homebrew_runtime_requirements_are_a_runtime_subset() -> None:
    repo_requirements = set(read_requirements(ROOT / "requirements.txt"))
    homebrew_requirements = read_requirements(HOMEBREW_REQUIREMENTS)

    assert set(homebrew_requirements).issubset(repo_requirements)
    assert all(not requirement.startswith("pytest") for requirement in homebrew_requirements)


def test_parse_downloaded_artifact_name_supports_wheels_and_sdists() -> None:
    assert parse_downloaded_artifact_name(
        "Kivy-2.3.1-cp312-cp312-macosx_10_15_universal2.whl"
    ) == ("Kivy", "2.3.1")
    assert parse_downloaded_artifact_name("kivymd-1.2.0.tar.gz") == ("kivymd", "1.2.0")


def test_render_formula_includes_expected_homebrew_runtime_wrapper() -> None:
    formula = render_formula(
        version="0.3.0",
        source_url="https://example.com/BatLLM.tar.gz",
        source_sha256="abc123",
        resources=[
            {
                "name": "Kivy",
                "url": "https://files.pythonhosted.org/packages/example/Kivy.whl",
                "sha256": "def456",
            }
        ],
    )

    assert 'depends_on "ollama"' in formula
    assert 'depends_on "python@3.12"' in formula
    assert 'resource "Kivy"' in formula
    assert 'export BATLLM_HOME="${BATLLM_HOME:-$HOME/Library/Application Support/BatLLM}"' in formula
    assert 'exec "#{libexec}/venv/bin/python" "#{pkgshare}/run_batllm.py" "$@"' in formula


def test_create_worktree_archive_contains_launchers(tmp_path: Path) -> None:
    archive_path = tmp_path / "batllm-worktree.tar.gz"

    create_worktree_archive(archive_path, prefix="BatLLM-worktree")

    with tarfile.open(archive_path, "r:gz") as archive:
        names = set(archive.getnames())

    assert "BatLLM-worktree/run_batllm.py" in names
    assert "BatLLM-worktree/src/main.py" in names