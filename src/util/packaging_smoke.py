"""Packaging smoke-validation helpers for BatLLM release workflows."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from tarfile import TarFile, open as tar_open
from zipfile import ZipFile


def read_version(root: Path) -> str:
    return (root / "VERSION").read_text(encoding="utf-8").strip()


def expected_release_artifact_paths(root: Path, version: str) -> dict[str, Path]:
    base = root / "dist" / "releases"
    return {
        "source_zip": base / f"BatLLM-v{version}-source.zip",
        "source_tgz": base / f"BatLLM-v{version}-source.tar.gz",
        "windows_zip": base / f"BatLLM-v{version}-windows.zip",
        "macos_zip": base / f"BatLLM-v{version}-macos.zip",
        "linux_tgz": base / f"BatLLM-v{version}-linux.tar.gz",
    }


def required_members_for_artifact(filename: str) -> tuple[str, ...]:
    if filename.endswith("-source.zip") or filename.endswith("-source.tar.gz"):
        return ("run_batllm.py", "run_game_analyzer.py")
    if filename.endswith("-windows.zip"):
        return ("install-batllm.bat", "run-batllm.bat", "run-game-analyzer.bat")
    if filename.endswith("-macos.zip"):
        return (
            "install-batllm.command",
            "run-batllm.command",
            "run-game-analyzer.command",
        )
    if filename.endswith("-linux.tar.gz"):
        return ("install-batllm.sh", "run-batllm.sh", "run-game-analyzer.sh")
    return ()


def archive_members(artifact_path: Path) -> set[str]:
    name = artifact_path.name
    if name.endswith(".zip"):
        with ZipFile(artifact_path, "r") as archive:
            return set(archive.namelist())

    if name.endswith(".tar.gz"):
        with tar_open(artifact_path, "r:gz") as archive:
            assert isinstance(archive, TarFile)
            return {member.name for member in archive.getmembers()}

    raise ValueError(f"Unsupported archive type: {artifact_path}")


def missing_required_members(artifact_path: Path, required: tuple[str, ...]) -> list[str]:
    members = archive_members(artifact_path)
    missing: list[str] = []
    for member in required:
        found = any(path == member or path.endswith(f"/{member}") for path in members)
        if not found:
            missing.append(member)
    return missing


def run_command(
    command: list[str],
    cwd: Path,
    *,
    env: dict[str, str] | None = None,
    timeout: float | None = None,
) -> tuple[int, str, str]:
    proc = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
        env=env,
        timeout=timeout,
    )
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def installer_artifact_key_for_current_platform() -> str:
    if sys.platform.startswith("win"):
        return "windows_zip"
    if sys.platform == "darwin":
        return "macos_zip"
    return "linux_tgz"


def installer_script_name_for_artifact(filename: str) -> str:
    if filename.endswith("-windows.zip"):
        return "install-batllm.bat"
    if filename.endswith("-macos.zip"):
        return "install-batllm.command"
    if filename.endswith("-linux.tar.gz"):
        return "install-batllm.sh"
    return ""


def _extract_archive(artifact_path: Path, destination: Path) -> None:
    name = artifact_path.name
    if name.endswith(".zip"):
        with ZipFile(artifact_path, "r") as archive:
            archive.extractall(destination)
        return
    if name.endswith(".tar.gz"):
        with tar_open(artifact_path, "r:gz") as archive:
            assert isinstance(archive, TarFile)
            archive.extractall(destination)
        return
    raise ValueError(f"Unsupported archive type: {artifact_path}")


def _run_installer_script(stage_root: Path, script_name: str, timeout_seconds: float) -> tuple[int, str, str]:
    if os.name == "nt":
        command = ["cmd.exe", "/c", script_name]
    else:
        command = ["bash", script_name]
    proc = subprocess.run(
        command,
        cwd=stage_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout_seconds,
    )
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def run_release_installer_smoke(
    root: Path,
    *,
    timeout_seconds: float,
    artifact_key: str | None = None,
) -> list[str]:
    errors: list[str] = []
    version = read_version(root)
    artifacts = expected_release_artifact_paths(root, version)
    selected_key = artifact_key or installer_artifact_key_for_current_platform()
    artifact_path = artifacts.get(selected_key)
    if artifact_path is None:
        return [f"unsupported installer smoke artifact key: {selected_key}"]
    if not artifact_path.exists():
        return [
            f"installer smoke requires an existing artifact; missing: {artifact_path}",
            "run create_release_bundles.py or validate_packaging_smoke.py without --skip-release-bundles first",
        ]

    script_name = installer_script_name_for_artifact(artifact_path.name)
    if not script_name:
        return [f"no installer script mapping for artifact: {artifact_path.name}"]

    with tempfile.TemporaryDirectory(prefix="batllm-installer-smoke-") as tmp_raw:
        tmp = Path(tmp_raw)
        _extract_archive(artifact_path, tmp)
        stage_root = tmp / artifact_path.name.removesuffix(".zip").removesuffix(".tar.gz")
        if not stage_root.exists():
            return [f"installer smoke failed: extracted stage not found: {stage_root}"]

        script_path = stage_root / script_name
        if not script_path.exists():
            return [f"installer smoke failed: missing installer script: {script_path}"]

        if os.name != "nt":
            script_path.chmod(script_path.stat().st_mode | 0o111)

        try:
            code, out, err = _run_installer_script(stage_root, script_name, timeout_seconds)
        except subprocess.TimeoutExpired:
            return [
                f"installer smoke failed: installer timed out after {timeout_seconds:.0f}s",
            ]

        if code != 0:
            errors.append(f"installer smoke failed: {script_name} exited with {code}")
            if out.strip():
                errors.append(out.strip())
            if err.strip():
                errors.append(err.strip())
            return errors

        if os.name == "nt":
            expected_python = stage_root / ".venv_BatLLM" / "Scripts" / "python.exe"
        else:
            expected_python = stage_root / ".venv_BatLLM" / "bin" / "python"
        if not expected_python.exists():
            errors.append(
                f"installer smoke failed: expected virtualenv python not found: {expected_python}"
            )

    return errors


def run_homebrew_install_smoke(
    root: Path,
    *,
    formula_path: Path,
    install_timeout_seconds: float,
) -> list[str]:
    errors: list[str] = []
    brew_env = {
        **os.environ,
        "HOMEBREW_NO_AUTO_UPDATE": "1",
        "HOMEBREW_NO_INSTALL_CLEANUP": "1",
        "HOMEBREW_NO_ENV_HINTS": "1",
    }

    code, out, err = run_command(["brew", "--repository"], cwd=root, env=brew_env)
    if code != 0:
        errors.append("homebrew install smoke failed: unable to resolve Homebrew repository")
        if out.strip():
            errors.append(out.strip())
        if err.strip():
            errors.append(err.strip())
        return errors

    tap_name = f"local/batllm-smoke-{os.getpid()}"
    tap_repo = Path(out.strip()) / "Library" / "Taps" / "local" / \
        f"homebrew-batllm-smoke-{os.getpid()}"
    tap_formula_dir = tap_repo / "Formula"
    tap_formula_path = tap_formula_dir / "batllm.rb"

    run_command(["brew", "untap", tap_name], cwd=root, env=brew_env)

    try:
        code, out, err = run_command(
            ["brew", "tap-new", "--no-git", tap_name], cwd=root, env=brew_env)
        if code != 0:
            errors.append(f"homebrew install smoke failed: brew tap-new failed for {tap_name}")
            if out.strip():
                errors.append(out.strip())
            if err.strip():
                errors.append(err.strip())
            return errors

        tap_formula_dir.mkdir(parents=True, exist_ok=True)
        tap_formula_path.write_text(formula_path.read_text(encoding="utf-8"), encoding="utf-8")

        run_command(["brew", "uninstall", "--force", "batllm"], cwd=root, env=brew_env)

        try:
            code, out, err = run_command(
                ["brew", "install", f"{tap_name}/batllm"],
                cwd=root,
                env=brew_env,
                timeout=install_timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            errors.append(
                f"homebrew install smoke failed: brew install timed out after {install_timeout_seconds:.0f}s"
            )
            return errors
        if code != 0:
            errors.append("homebrew install smoke failed: brew install returned non-zero")
            if out.strip():
                errors.append(out.strip())
            if err.strip():
                errors.append(err.strip())
            return errors

        code, out, err = run_command(["brew", "test", "batllm"], cwd=root, env=brew_env)
        if code != 0:
            errors.append("homebrew install smoke failed: brew test batllm returned non-zero")
            if out.strip():
                errors.append(out.strip())
            if err.strip():
                errors.append(err.strip())
            return errors
    finally:
        run_command(["brew", "uninstall", "--force", "batllm"], cwd=root, env=brew_env)
        run_command(["brew", "untap", tap_name], cwd=root, env=brew_env)

    return errors


def run_packaging_smoke(
    root: Path,
    *,
    python_executable: str,
    run_release: bool,
    run_homebrew: bool,
    run_homebrew_install_check: bool,
    run_installer_smoke: bool,
    installer_timeout_seconds: float,
    homebrew_install_timeout_seconds: float,
) -> list[str]:
    errors: list[str] = []

    if run_release:
        code, out, err = run_command([python_executable, "create_release_bundles.py"], cwd=root)
        if code != 0:
            errors.append("create_release_bundles.py failed")
            if out.strip():
                errors.append(out.strip())
            if err.strip():
                errors.append(err.strip())
        else:
            version = read_version(root)
            for artifact in expected_release_artifact_paths(root, version).values():
                if not artifact.exists():
                    errors.append(f"missing release artifact: {artifact}")
                    continue
                required = required_members_for_artifact(artifact.name)
                missing = missing_required_members(artifact, required)
                if missing:
                    errors.append(
                        f"{artifact.name} is missing expected members: {', '.join(missing)}"
                    )

    if run_homebrew or run_homebrew_install_check:
        with tempfile.TemporaryDirectory(prefix="batllm-packaging-smoke-") as tmp_raw:
            tmp = Path(tmp_raw)
            archive_path = tmp / "BatLLM-homebrew-source.tar.gz"
            formula_path = tmp / "batllm.rb"
            code, out, err = run_command(
                [
                    python_executable,
                    "create_homebrew_formula.py",
                    "--create-worktree-archive",
                    str(archive_path),
                    "--formula-out",
                    str(formula_path),
                ],
                cwd=root,
            )
            if code != 0:
                errors.append("create_homebrew_formula.py dry-run failed")
                if out.strip():
                    errors.append(out.strip())
                if err.strip():
                    errors.append(err.strip())
            else:
                if not formula_path.exists():
                    errors.append(f"missing generated Homebrew formula: {formula_path}")
                else:
                    if run_homebrew:
                        text = formula_path.read_text(encoding="utf-8")
                        for needle in ('bin/"batllm"', 'bin/"batllm-analyzer"', 'depends_on "ollama"'):
                            if needle not in text:
                                errors.append(
                                    f"generated formula missing expected content: {needle}")
                    if run_homebrew_install_check:
                        errors.extend(
                            run_homebrew_install_smoke(
                                root,
                                formula_path=formula_path,
                                install_timeout_seconds=homebrew_install_timeout_seconds,
                            )
                        )

    if run_installer_smoke:
        errors.extend(
            run_release_installer_smoke(
                root,
                timeout_seconds=installer_timeout_seconds,
            )
        )

    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run BatLLM packaging smoke validation")
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable used to run packaging scripts.",
    )
    parser.add_argument(
        "--skip-release-bundles",
        action="store_true",
        help="Skip create_release_bundles.py smoke validation.",
    )
    parser.add_argument(
        "--skip-homebrew",
        action="store_true",
        help="Skip create_homebrew_formula.py dry-run smoke validation.",
    )
    parser.add_argument(
        "--run-homebrew-install-smoke",
        action="store_true",
        help=(
            "Run Homebrew install/test/uninstall smoke using a temporary local tap and the generated formula. "
            "This is slower than dry-run validation."
        ),
    )
    parser.add_argument(
        "--homebrew-install-timeout",
        type=float,
        default=1800.0,
        help="Timeout in seconds for Homebrew install during install-level smoke.",
    )
    parser.add_argument(
        "--run-installer-smoke",
        action="store_true",
        help=(
            "Run an install-script smoke test using the current platform release bundle in a temp directory. "
            "This executes the packaged install wrapper and verifies the created virtualenv."
        ),
    )
    parser.add_argument(
        "--installer-timeout",
        type=float,
        default=900.0,
        help="Timeout in seconds for the installer smoke script execution.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    errors = run_packaging_smoke(
        root,
        python_executable=args.python,
        run_release=not args.skip_release_bundles,
        run_homebrew=not args.skip_homebrew,
        run_homebrew_install_check=args.run_homebrew_install_smoke,
        run_installer_smoke=args.run_installer_smoke,
        installer_timeout_seconds=float(args.installer_timeout),
        homebrew_install_timeout_seconds=float(args.homebrew_install_timeout),
    )
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("Packaging smoke validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
