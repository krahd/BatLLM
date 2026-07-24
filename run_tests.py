"""Cross-platform test runner for BatLLM."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
PROJECT_VENV_PYTHON = (
    ROOT / ".venv_BatLLM" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
)
PYTHON = PROJECT_VENV_PYTHON if PROJECT_VENV_PYTHON.exists() else Path(sys.executable)

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from util.compat import require_supported_python  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(description="Cross-platform BatLLM test runner")
    parser.add_argument(
        "mode",
        nargs="?",
        default="non-live",
        choices=("core", "non-live", "full"),
        help="core: minimal smoke; non-live: complete isolated suite; full: suite plus live Ollama tests",
    )
    return parser


def run_pytest(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    """Run pytest through the project venv, or the active interpreter as a fallback."""
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    merged_env.setdefault("PYTHONPATH", "src")
    return subprocess.run(
        [str(PYTHON), "-m", "pytest", "-q", *args],
        cwd=ROOT,
        text=True,
        check=False,
        env=merged_env,
    )


def run_llm_service(*args: str) -> subprocess.CompletedProcess:
    """Run llm.service through the selected interpreter with src on PYTHONPATH."""
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", "src")
    return subprocess.run(
        [str(PYTHON), "-m", "llm.service", *args],
        cwd=ROOT,
        text=True,
        check=False,
        env=env,
    )


def main(argv: list[str] | None = None) -> int:
    """Entry point for the cross-platform test runner."""
    require_supported_python()
    parser = build_parser()
    args = parser.parse_args(argv)

    core = run_pytest("src/tests/test_history_compact.py")
    if core.returncode != 0 or args.mode == "core":
        sys.stdout.write(core.stdout or "")
        sys.stderr.write(core.stderr or "")
        return core.returncode

    if args.mode == "non-live":
        suite = run_pytest("src/tests")
        sys.stdout.write(suite.stdout or "")
        sys.stderr.write(suite.stderr or "")
        return suite.returncode

    start_proc = run_llm_service("start")
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
        run_llm_service("stop", "-v")


if __name__ == "__main__":
    raise SystemExit(main())
