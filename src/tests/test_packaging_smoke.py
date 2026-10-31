from __future__ import annotations

import tarfile
import os
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

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


@pytest.mark.skipif(os.name == "nt", reason="POSIX installer execution")
@pytest.mark.parametrize("supported_available", [True, False])
def test_bundle_installer_skips_unsupported_default(tmp_path, supported_available):
    from create_release_bundles import macos_wrapper_contents

    bundle = tmp_path / "Bundle with spaces"
    bundle.mkdir()
    script = bundle / "install-batllm.command"
    script.write_text(macos_wrapper_contents("0.3.6")[script.name])
    commands = tmp_path / "commands"
    commands.mkdir()
    (commands / "dirname").symlink_to(shutil.which("dirname"))
    log = tmp_path / "commands.log"

    # Test interpreter discovery without creating environments or using pip.
    for name, supported in (("python3", False), ("python3.12", supported_available)):
        candidate = commands / name
        candidate.write_text(
            f"#!{sys.executable}\n"
            "import sys\nfrom pathlib import Path\n"
            f"with Path({str(log)!r}).open('a') as log:\n"
            f"    log.write({name!r} + ' ' + ' '.join(sys.argv[1:]) + '\\n')\n"
            f"if not {supported!r}: sys.exit(1)\n"
            "if sys.argv[1:3] == ['-m', 'venv']:\n"
            "    target = Path(sys.argv[3]) / 'bin' / 'python'\n"
            "    target.parent.mkdir(parents=True)\n"
            "    target.write_text(Path(__file__).read_text())\n"
            "    target.chmod(0o755)\n"
        )
        candidate.chmod(0o755)

    result = subprocess.run(
        [shutil.which("bash"), str(script)], cwd=tmp_path,
        env={**os.environ, "PATH": str(commands)}, capture_output=True, text=True, check=False,
    )
    calls = log.read_text()
    assert "python3 -m" not in calls
    if supported_available:
        assert result.returncode == 0, result.stderr
        assert "python3.12 -m venv .venv_BatLLM" in calls
        assert (bundle / ".venv_BatLLM/bin/python").exists()
    else:
        assert result.returncode != 0
        assert "Install Python 3.10, 3.11, or 3.12" in result.stderr
        assert "-m venv" not in calls and "-m pip" not in calls
        assert not (bundle / ".venv_BatLLM").exists()


@pytest.mark.parametrize("returncode", [0, 1])
def test_installer_smoke_checks_created_python(monkeypatch, tmp_path, returncode):
    (tmp_path / "VERSION").write_text("0.3.6")
    archive = packaging_smoke.expected_release_artifact_paths(tmp_path, "0.3.6")["macos_zip"]
    archive.parent.mkdir(parents=True)
    with ZipFile(archive, "w") as bundle:
        bundle.writestr("BatLLM-v0.3.6-macos/install-batllm.command", "exit 0\n")

    def installed(stage, *_args):
        python = stage / ".venv_BatLLM" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        python.parent.mkdir(parents=True)
        python.touch()
        return 0, "", ""

    def check_python(command, cwd, **_kwargs):
        assert Path(command[0]).is_relative_to(cwd / ".venv_BatLLM")
        assert command[1:] == ["src/util/compat.py"]
        return returncode, "", "Detected Python 3.15.2." if returncode else ""

    monkeypatch.setattr(packaging_smoke, "_run_installer_script", installed)
    monkeypatch.setattr(packaging_smoke, "run_command", check_python)
    errors = packaging_smoke.run_release_installer_smoke(
        tmp_path, timeout_seconds=10, artifact_key="macos_zip")
    if returncode:
        assert errors and "Detected Python 3.15.2." in errors
    else:
        assert not errors


@pytest.mark.parametrize("version, returncode", [((3, 12, 0), 0), ((3, 15, 2), 1)])
def test_installer_python_probe_uses_launcher_version_bounds(version, returncode):
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "-c",
         f"import runpy, sys; sys.version_info = {version!r}; "
         "runpy.run_path('src/util/compat.py', run_name='__main__')"],
        cwd=root, capture_output=True, text=True, check=False,
    )
    assert result.returncode == returncode
    if returncode:
        assert "requires Python 3.10 through 3.12" in result.stderr
