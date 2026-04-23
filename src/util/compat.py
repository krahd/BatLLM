"""Compatibility helpers.

Keep a single place for small runtime checks such as Python version
requirements so entry scripts can import and run them early.
"""
from __future__ import annotations

import sys

MIN_PYTHON: tuple[int, int] = (3, 10)


def require_supported_python(app_name: str = "BatLLM") -> None:
    """Exit early with a clear message on unsupported Python versions.

    Args:
        app_name: Display name used in the error message.
    """
    if sys.version_info >= MIN_PYTHON:
        return
    version = ".".join(str(part) for part in sys.version_info[:3])
    raise SystemExit(
        f"{app_name} requires Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer. "
        f"Detected Python {version}."
    )
