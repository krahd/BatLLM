"""Cross-platform launcher for BatLLM."""

from __future__ import annotations
from util.compat import require_supported_python

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


require_supported_python("BatLLM")

from main import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
