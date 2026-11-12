from __future__ import annotations

from importlib import import_module
import sys
import tarfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

paths = import_module("util.paths")
ollama_service = import_module("llm.service")
AppConfig = import_module("configs.app_config").AppConfig
_homebrew_formula = import_module("create_homebrew_formula")
create_worktree_archive = _homebrew_formula.create_worktree_archive
parse_downloaded_artifact_name = _homebrew_formula.parse_downloaded_artifact_name
read_requirements = _homebrew_formula.read_requirements
read_version = _homebrew_formula.read_version
render_formula = _homebrew_formula.render_formula



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
        version=read_version(),
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


def test_formula_accepts_only_apple_silicon_or_pure_python_artifacts() -> None:
    compatible = _homebrew_formula.is_formula_compatible_artifact

    assert compatible("Kivy-2.3.1-cp312-cp312-macosx_10_15_universal2.whl")
    assert compatible("psutil-7.2.2-cp36-abi3-macosx_11_0_arm64.whl")
    assert compatible("requests-2.34.2-py3-none-any.whl")
    assert compatible("kivymd-1.2.0.tar.gz")
    # Alternative platform tags: one Apple Silicon tag is sufficient.
    assert compatible(
        "maturin-1.12.6-py3-none-macosx_10_12_x86_64.macosx_11_0_arm64.macosx_10_12_universal2.whl"
    )
    assert not compatible(
        "Kivy-2.3.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"
    )
    assert not compatible("psutil-7.2.2-cp36-abi3-macosx_10_9_x86_64.whl")
    assert not compatible("PyYAML-6.0.3-cp312-cp312-win_amd64.whl")
    # The formula's environment is Python 3.12.
    assert not compatible("Kivy-2.3.1-cp311-cp311-macosx_10_15_universal2.whl")
    assert not compatible("example-1.0-cp313-abi3-macosx_11_0_arm64.whl")
    assert compatible("requests-2.34.2-py2.py3-none-any.whl")


def test_resource_resolution_rejects_foreign_platform_wheels(monkeypatch) -> None:
    """A Linux resolution must fail before any formula resource is recorded."""
    foreign = "Kivy-2.3.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"

    def fake_pip_download(command, **_kwargs):
        destination = Path(command[command.index("--dest") + 1])
        (destination / foreign).write_bytes(b"")
        (destination / "requests-2.34.2-py3-none-any.whl").write_bytes(b"")

    looked_up = []
    monkeypatch.setattr(_homebrew_formula.subprocess, "run", fake_pip_download)
    monkeypatch.setattr(
        _homebrew_formula, "pypi_release_file", lambda *args: looked_up.append(args)
    )

    try:
        _homebrew_formula.resolve_runtime_resources(["Kivy==2.3.1"], python_executable="python")
    except SystemExit as exc:
        message = str(exc)
    else:
        raise AssertionError("foreign-platform wheels were accepted")

    assert foreign in message
    assert "Apple Silicon macOS" in message
    assert not looked_up


def test_resource_resolution_accepts_apple_silicon_wheels(monkeypatch) -> None:
    names = [
        "Kivy-2.3.1-cp312-cp312-macosx_10_15_universal2.whl",
        "kivymd-1.2.0.tar.gz",
    ]

    def fake_pip_download(command, **_kwargs):
        destination = Path(command[command.index("--dest") + 1])
        for name in names:
            (destination / name).write_bytes(b"")

    monkeypatch.setattr(_homebrew_formula.subprocess, "run", fake_pip_download)
    monkeypatch.setattr(
        _homebrew_formula,
        "pypi_release_file",
        lambda project, version, filename: {
            "name": project, "url": f"https://example.invalid/{filename}",
            "sha256": "0" * 64, "filename": filename, "packagetype": "bdist_wheel",
        },
    )

    resources = _homebrew_formula.resolve_runtime_resources(
        ["Kivy==2.3.1"], python_executable="python"
    )

    assert sorted(resource["filename"] for resource in resources) == sorted(names)


def test_publish_workflow_renders_formula_on_apple_silicon_macos() -> None:
    workflow = yaml.safe_load(
        (ROOT / ".github/workflows/publish-homebrew-tap.yml").read_text(encoding="utf-8")
    )
    job = workflow["jobs"]["publish"]
    step_names = [step.get("name") for step in job["steps"]]

    assert str(job["runs-on"]).startswith("macos-")
    assert _setup_python_version(job) == "3.12"
    assert job["if"] == "github.repository == 'krahd/BatLLM'"
    assert step_names.index("Confirm Apple Silicon macOS runner") < step_names.index(
        "Render formula"
    )


def _setup_python_version(job: dict) -> str:
    versions = [
        str(step["with"]["python-version"])
        for step in job["steps"]
        if "setup-python" in str(step.get("uses", ""))
    ]
    assert len(versions) == 1
    return versions[0]


def test_ci_dry_run_renders_formula_on_the_formula_target() -> None:
    workflow = yaml.safe_load(
        (ROOT / ".github/workflows/multiplatform.yml").read_text(encoding="utf-8")
    )
    job = workflow["jobs"]["homebrew"]

    assert str(job["runs-on"]).startswith("macos-")
    assert _setup_python_version(job) == "3.12"
