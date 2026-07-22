"""Shared paths and fixtures for the URUCON evaluation."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def repository_commit() -> str | None:
    """Return the checked-out source revision when Git metadata is available."""

    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def initial_state(offset: float = 0.0) -> dict[int, dict[str, object]]:
    return {
        1: {
            "id": 1,
            "health": 30,
            "x": 0.2 + offset,
            "y": 0.5,
            "rot": 0,
            "shield": False,
        },
        2: {
            "id": 2,
            "health": 30,
            "x": 0.8 - offset,
            "y": 0.5,
            "rot": 180,
            "shield": False,
        },
    }
