"""Cross-platform launcher for the standalone BatLLM Game Analyzer."""

from __future__ import annotations

import sys
from pathlib import Path


MIN_PYTHON = (3, 10)
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"


def require_supported_python() -> None:
    """Exit early with a clear message on unsupported Python versions."""
    if sys.version_info >= MIN_PYTHON:
        return
    version = ".".join(str(part) for part in sys.version_info[:3])
    raise SystemExit(f"BatLLM Game Analyzer requires Python 3.10 or newer. Detected Python {version}.")


require_supported_python()

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from analyzer_main import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
