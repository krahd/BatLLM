from __future__ import annotations

import tarfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from util import packaging_smoke


def test_required_members_for_platform_bundles_include_analyzer_launchers() -> None:
    assert "run-game-analyzer.bat" in packaging_smoke.required_members_for_artifact(
        "BatLLM-v0.3.4-windows.zip"
    )
    assert "run-game-analyzer.command" in packaging_smoke.required_members_for_artifact(
        "BatLLM-v0.3.4-macos.zip"
    )
    assert "run-game-analyzer.sh" in packaging_smoke.required_members_for_artifact(
        "BatLLM-v0.3.4-linux.tar.gz"
    )


def test_missing_required_members_detects_missing_files_in_zip(tmp_path: Path) -> None:
    archive_path = tmp_path / "bundle.zip"
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("BatLLM-v0.3.4-windows/run-batllm.bat", "echo ok")

    missing = packaging_smoke.missing_required_members(
        archive_path,
        ("run-batllm.bat", "run-game-analyzer.bat"),
    )

    assert missing == ["run-game-analyzer.bat"]


def test_missing_required_members_detects_missing_files_in_tar(tmp_path: Path) -> None:
    stage = tmp_path / "stage"
    stage.mkdir(parents=True, exist_ok=True)
    (stage / "run-batllm.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    archive_path = tmp_path / "bundle.tar.gz"
    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(stage / "run-batllm.sh", arcname="BatLLM-v0.3.4-linux/run-batllm.sh")

    missing = packaging_smoke.missing_required_members(
        archive_path,
        ("run-batllm.sh", "run-game-analyzer.sh"),
    )

    assert missing == ["run-game-analyzer.sh"]


def test_expected_release_artifact_paths_uses_versioned_dist_layout(tmp_path: Path) -> None:
    paths = packaging_smoke.expected_release_artifact_paths(tmp_path, "0.3.4")

    assert paths["source_zip"] == tmp_path / "dist" / "releases" / "BatLLM-v0.3.4-source.zip"
    assert paths["linux_tgz"] == tmp_path / "dist" / "releases" / "BatLLM-v0.3.4-linux.tar.gz"


def test_installer_artifact_key_for_platform_maps_expected(monkeypatch) -> None:
    monkeypatch.setattr(packaging_smoke.sys, "platform", "darwin")
    assert packaging_smoke.installer_artifact_key_for_current_platform() == "macos_zip"

    monkeypatch.setattr(packaging_smoke.sys, "platform", "win32")
    assert packaging_smoke.installer_artifact_key_for_current_platform() == "windows_zip"

    monkeypatch.setattr(packaging_smoke.sys, "platform", "linux")
    assert packaging_smoke.installer_artifact_key_for_current_platform() == "linux_tgz"


def test_installer_script_name_for_artifact_maps_expected() -> None:
    assert packaging_smoke.installer_script_name_for_artifact(
        "BatLLM-v0.3.4-windows.zip") == "install-batllm.bat"
    assert packaging_smoke.installer_script_name_for_artifact(
        "BatLLM-v0.3.4-macos.zip") == "install-batllm.command"
    assert packaging_smoke.installer_script_name_for_artifact(
        "BatLLM-v0.3.4-linux.tar.gz") == "install-batllm.sh"


def test_run_packaging_smoke_calls_installer_smoke_when_enabled(monkeypatch, tmp_path: Path) -> None:
    called = {}
    monkeypatch.setattr(packaging_smoke, "run_command", lambda *_args, **_kwargs: (0, "", ""))
    monkeypatch.setattr(
        packaging_smoke,
        "run_release_installer_smoke",
        lambda _root, timeout_seconds, artifact_key=None: called.update(
            {"timeout_seconds": timeout_seconds, "artifact_key": artifact_key}
        ) or [],
    )

    errors = packaging_smoke.run_packaging_smoke(
        tmp_path,
        python_executable="python3",
        run_release=False,
        run_homebrew=False,
        run_homebrew_install_check=False,
        run_installer_smoke=True,
        installer_timeout_seconds=321.0,
        homebrew_install_timeout_seconds=999.0,
    )

    assert errors == []
    assert called == {"timeout_seconds": 321.0, "artifact_key": None}


def test_run_packaging_smoke_calls_homebrew_install_smoke_when_enabled(monkeypatch, tmp_path: Path) -> None:
    called = {}

    def _fake_run_command(command, cwd, **_kwargs):
        _ = cwd
        if command and command[1:2] == ["create_homebrew_formula.py"]:
            archive_path = Path(command[3])
            formula_path = Path(command[5])
            archive_path.write_text("archive", encoding="utf-8")
            formula_path.write_text(
                'depends_on "ollama"\nbin/"batllm"\nbin/"batllm-analyzer"\n', encoding="utf-8")
        return 0, "", ""

    monkeypatch.setattr(packaging_smoke, "run_command", _fake_run_command)
    monkeypatch.setattr(
        packaging_smoke,
        "run_homebrew_install_smoke",
        lambda _root, formula_path, install_timeout_seconds: called.update(
            {
                "formula_exists": Path(formula_path).exists(),
                "install_timeout_seconds": install_timeout_seconds,
            }
        ) or [],
    )

    errors = packaging_smoke.run_packaging_smoke(
        tmp_path,
        python_executable="python3",
        run_release=False,
        run_homebrew=False,
        run_homebrew_install_check=True,
        run_installer_smoke=False,
        installer_timeout_seconds=111.0,
        homebrew_install_timeout_seconds=456.0,
    )

    assert errors == []
    assert called == {"formula_exists": True, "install_timeout_seconds": 456.0}


def test_run_homebrew_install_smoke_reports_missing_brew(monkeypatch, tmp_path: Path) -> None:
    formula_path = tmp_path / "batllm.rb"
    formula_path.write_text("class Batllm < Formula\nend\n", encoding="utf-8")

    def _missing_brew(*_args, **_kwargs):
        raise FileNotFoundError("brew")

    monkeypatch.setattr(packaging_smoke, "run_command", _missing_brew)

    errors = packaging_smoke.run_homebrew_install_smoke(
        tmp_path,
        formula_path=formula_path,
        install_timeout_seconds=60.0,
    )

    assert errors == ["homebrew install smoke failed: brew command not found on PATH"]
