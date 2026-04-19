"""Cross-platform test runner for BatLLM."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


MIN_PYTHON = (3, 10)
ROOT = Path(__file__).resolve().parent
VENV_PYTHON = (
    ROOT / ".venv_BatLLM" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
)
OLLAMA_HELPER = ROOT / "src" / "ollama_service.py"


def require_supported_python() -> None:
    """Exit early with a clear message on unsupported Python versions."""
    if sys.version_info >= MIN_PYTHON:
        return
    version = ".".join(str(part) for part in sys.version_info[:3])
    raise SystemExit(f"BatLLM requires Python 3.10 or newer. Detected Python {version}.")


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(description="Cross-platform BatLLM test runner")
    parser.add_argument(
        "mode",
        nargs="?",
        default="core",
        choices=("core", "full"),
        help="core: smoke checks only; full: smoke checks plus live Ollama integration tests",
    )
    return parser


def run_pytest(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    """Run pytest through the project virtual environment."""
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    merged_env.setdefault("PYTHONPATH", "src")
    return subprocess.run(
        [str(VENV_PYTHON), "-m", "pytest", "-q", *args],
        cwd=ROOT,
        text=True,
        check=False,
        env=merged_env,
    )


def main(argv: list[str] | None = None) -> int:
    """Entry point for the cross-platform test runner."""
    require_supported_python()
    parser = build_parser()
    args = parser.parse_args(argv)

    if not VENV_PYTHON.exists():
        print(
            f"Error: {VENV_PYTHON} not found. Create the venv first with "
            f"`{sys.executable} -m venv .venv_BatLLM`.",
            file=sys.stderr,
        )
        return 1

    core = run_pytest("src/tests/test_history_compact.py")
    if core.returncode != 0 or args.mode == "core":
        sys.stdout.write(core.stdout or "")
        sys.stderr.write(core.stderr or "")
        return core.returncode

    start_proc = subprocess.run(
        [str(VENV_PYTHON), "-m", "llm.service", "start"],
        cwd=ROOT,
        text=True,
        check=False,
    )
    if start_proc.returncode != 0:
        sys.stdout.write(start_proc.stdout or "")
        sys.stderr.write(start_proc.stderr or "")
        return start_proc.returncode

    try:
        full = run_pytest("src/tests", env={"BATLLM_RUN_OLLAMA_SMOKE": "1"})
        sys.stdout.write(full.stdout or "")
        sys.stderr.write(full.stderr or "")
        return full.returncode
    finally:
        subprocess.run(
            [str(VENV_PYTHON), "-m", "llm.service", "stop", "-v"],
            cwd=ROOT,
            text=True,
            check=False,
        )


if __name__ == "__main__":
    raise SystemExit(main())
