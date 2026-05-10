"""Compatibility helpers.

Keep a single place for small runtime checks such as Python version
requirements so entry scripts can import and run them early.
"""
from __future__ import annotations

import sys

MIN_PYTHON: tuple[int, int] = (3, 10)
MAX_PYTHON_EXCLUSIVE: tuple[int, int] = (3, 13)


def require_supported_python(app_name: str = "BatLLM") -> None:
    """Exit early with a clear message on unsupported Python versions.

    Args:
        app_name: Display name used in the error message.
    """
    if MIN_PYTHON <= sys.version_info < MAX_PYTHON_EXCLUSIVE:
        return
    version = ".".join(str(part) for part in sys.version_info[:3])
    supported = (
        f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]} through "
        f"{MAX_PYTHON_EXCLUSIVE[0]}.{MAX_PYTHON_EXCLUSIVE[1] - 1}"
    )
    raise SystemExit(
        f"{app_name} requires Python {supported}. "
        f"Detected Python {version}."
    )
