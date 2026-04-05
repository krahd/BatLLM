"""Version helpers for BatLLM applications."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERSION_FILE = ROOT / "VERSION"


@lru_cache(maxsize=1)
def current_app_version() -> str:
    """Return the repository version string."""
    try:
        version = VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        version = ""

    return version or "0.0.0"
