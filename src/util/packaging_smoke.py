"""Packaging smoke-validation helpers for BatLLM release workflows."""

from __future__ import annotations

import argparse
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


def run_command(command: list[str], cwd: Path) -> tuple[int, str, str]:
    proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def run_packaging_smoke(root: Path, *, python_executable: str, run_release: bool, run_homebrew: bool) -> list[str]:
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

    if run_homebrew:
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
                    text = formula_path.read_text(encoding="utf-8")
                    for needle in ('bin/"batllm"', 'bin/"batllm-analyzer"', 'depends_on "ollama"'):
                        if needle not in text:
                            errors.append(f"generated formula missing expected content: {needle}")

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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    errors = run_packaging_smoke(
        root,
        python_executable=args.python,
        run_release=not args.skip_release_bundles,
        run_homebrew=not args.skip_homebrew,
    )
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("Packaging smoke validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
