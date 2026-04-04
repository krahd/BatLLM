"""Create BatLLM source and platform release bundles."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parent
DIST_DIR = ROOT / "dist" / "releases"
VERSION_FILE = ROOT / "VERSION"


def read_version() -> str:
    """Read the release version from ``VERSION``."""
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def tracked_files() -> list[Path]:
    """Return the tracked repository files that should be shipped in a release bundle."""
    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        capture_output=True,
        text=False,
        check=True,
    )
    entries = [entry.decode("utf-8") for entry in proc.stdout.split(b"\0") if entry]
    return [ROOT / entry for entry in entries]


def platform_note(version: str, platform_name: str, install_hint: str) -> str:
    """Create a small platform-specific release note."""
    return (
        f"BatLLM {version} - {platform_name} release bundle\n\n"
        "Quick start:\n"
        "1. Install Python 3.10 or newer. Python 3.11 or 3.12 is recommended.\n"
        "2. Install Ollama from the official download page for your platform.\n"
        "3. Run the included install script.\n"
        "4. Launch BatLLM with the included run script.\n\n"
        f"Ollama guidance: {install_hint}\n"
    )


def windows_wrapper_contents(version: str) -> dict[str, str]:
    """Return the Windows-specific wrapper files."""
    return {
        "install-batllm.bat": (
            "@echo off\r\n"
            "setlocal\r\n"
            "cd /d %~dp0\r\n"
            "where py >nul 2>nul && (set PY_CMD=py) || (set PY_CMD=python)\r\n"
            "%PY_CMD% -m venv .venv_BatLLM\r\n"
            "if errorlevel 1 exit /b 1\r\n"
            ".\\.venv_BatLLM\\Scripts\\python -m pip install --upgrade pip\r\n"
            "if errorlevel 1 exit /b 1\r\n"
            ".\\.venv_BatLLM\\Scripts\\python -m pip install -r requirements.txt\r\n"
        ),
        "run-batllm.bat": (
            "@echo off\r\n"
            "setlocal\r\n"
            "cd /d %~dp0\r\n"
            "if exist .\\.venv_BatLLM\\Scripts\\python.exe (\r\n"
            "  .\\.venv_BatLLM\\Scripts\\python.exe run_batllm.py %*\r\n"
            ") else (\r\n"
            "  python run_batllm.py %*\r\n"
            ")\r\n"
        ),
        "WINDOWS_RELEASE_NOTES.txt": platform_note(
            version,
            "Windows",
            "https://ollama.com/download/windows",
        ).replace("\n", "\r\n"),
    }


def macos_wrapper_contents(version: str) -> dict[str, str]:
    """Return the macOS-specific wrapper files."""
    return {
        "install-batllm.command": (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "cd \"$(dirname \"$0\")\"\n"
            "python3 -m venv .venv_BatLLM\n"
            "./.venv_BatLLM/bin/python -m pip install --upgrade pip\n"
            "./.venv_BatLLM/bin/python -m pip install -r requirements.txt\n"
        ),
        "run-batllm.command": (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "cd \"$(dirname \"$0\")\"\n"
            "if [[ -x ./.venv_BatLLM/bin/python ]]; then\n"
            "  exec ./.venv_BatLLM/bin/python run_batllm.py \"$@\"\n"
            "fi\n"
            "exec python3 run_batllm.py \"$@\"\n"
        ),
        "MACOS_RELEASE_NOTES.txt": platform_note(
            version,
            "macOS",
            "https://ollama.com/download",
        ),
    }


def linux_wrapper_contents(version: str) -> dict[str, str]:
    """Return the Linux-specific wrapper files."""
    return {
        "install-batllm.sh": (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "cd \"$(dirname \"$0\")\"\n"
            "python3 -m venv .venv_BatLLM\n"
            "./.venv_BatLLM/bin/python -m pip install --upgrade pip\n"
            "./.venv_BatLLM/bin/python -m pip install -r requirements.txt\n"
        ),
        "run-batllm.sh": (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "cd \"$(dirname \"$0\")\"\n"
            "if [[ -x ./.venv_BatLLM/bin/python ]]; then\n"
            "  exec ./.venv_BatLLM/bin/python run_batllm.py \"$@\"\n"
            "fi\n"
            "exec python3 run_batllm.py \"$@\"\n"
        ),
        "LINUX_RELEASE_NOTES.txt": platform_note(
            version,
            "Linux",
            "https://ollama.com/download/linux",
        ),
    }


def write_text_file(path: Path, contents: str) -> None:
    """Write a text file, preserving executable bits for shell wrappers."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8", newline="")
    if path.suffix in {".sh", ".command"}:
        path.chmod(0o755)


def stage_release(base_name: str, extra_files: dict[str, str] | None = None) -> Path:
    """Stage the tracked tree plus any generated platform files into a temp directory."""
    tempdir = Path(tempfile.mkdtemp(prefix="batllm-release-"))
    stage_root = tempdir / base_name
    stage_root.mkdir(parents=True, exist_ok=True)

    for src in tracked_files():
        rel = src.relative_to(ROOT)
        dest = stage_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    for rel, contents in (extra_files or {}).items():
        write_text_file(stage_root / rel, contents)

    return stage_root


def build_zip(stage_root: Path, output_path: Path) -> None:
    """Create a zip archive from a staged release directory."""
    with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as archive:
        for path in stage_root.rglob("*"):
            archive.write(path, arcname=path.relative_to(stage_root.parent))


def build_tar_gz(stage_root: Path, output_path: Path) -> None:
    """Create a gzipped tar archive from a staged release directory."""
    with tarfile.open(output_path, "w:gz") as archive:
        archive.add(stage_root, arcname=stage_root.name)


def create_bundles(version: str) -> list[Path]:
    """Create the source and platform release bundles and return their paths."""
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []

    source_base = f"BatLLM-v{version}-source"
    source_stage = stage_release(source_base)
    source_zip = DIST_DIR / f"{source_base}.zip"
    source_tgz = DIST_DIR / f"{source_base}.tar.gz"
    build_zip(source_stage, source_zip)
    build_tar_gz(source_stage, source_tgz)
    outputs.extend((source_zip, source_tgz))

    windows_base = f"BatLLM-v{version}-windows"
    windows_stage = stage_release(windows_base, windows_wrapper_contents(version))
    windows_zip = DIST_DIR / f"{windows_base}.zip"
    build_zip(windows_stage, windows_zip)
    outputs.append(windows_zip)

    macos_base = f"BatLLM-v{version}-macos"
    macos_stage = stage_release(macos_base, macos_wrapper_contents(version))
    macos_zip = DIST_DIR / f"{macos_base}.zip"
    build_zip(macos_stage, macos_zip)
    outputs.append(macos_zip)

    linux_base = f"BatLLM-v{version}-linux"
    linux_stage = stage_release(linux_base, linux_wrapper_contents(version))
    linux_tgz = DIST_DIR / f"{linux_base}.tar.gz"
    build_tar_gz(linux_stage, linux_tgz)
    outputs.append(linux_tgz)

    return outputs


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(description="Create BatLLM release bundles")
    parser.add_argument(
        "--version",
        default=read_version() if VERSION_FILE.exists() else None,
        help="Release version to package. Defaults to the contents of VERSION.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the release bundle generator."""
    parser = build_parser()
    args = parser.parse_args(argv)
    version = (args.version or "").strip()
    if not version:
        parser.error("A version is required. Create VERSION or pass --version.")

    outputs = create_bundles(version)
    for output in outputs:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
