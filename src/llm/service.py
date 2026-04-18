"""Centralized Ollama/modelito lifecycle helpers.

This module prefers `modelito.ollama_service` when available, otherwise it
delegates to the local `ollama_service` implementation. Callers should use
this module as the canonical lifecycle API (`start_service`,
`stop_service`, `inspect_service_state`, `install_service`, `run_ollama_command`).
"""
from __future__ import annotations

from typing import Any
import importlib
import logging
import subprocess
from pathlib import Path

_logger = logging.getLogger(__name__)


def _load_modelito_impl():
    try:
        import modelito  # type: ignore

        svc = getattr(modelito, "ollama_service", None)
        if svc is None:
            return None
        return svc
    except Exception:
        return None


def _load_local_impl():
    try:
        # Import the existing ollama_service module from the package root.
        return importlib.import_module("ollama_service")
    except Exception as exc:
        _logger.debug("Failed to import local ollama_service: %s", exc)
        return None


_MODELITO = _load_modelito_impl()
_LOCAL = None if _MODELITO is not None else _load_local_impl()


def inspect_service_state(config_path: Path | None = None) -> dict[str, object]:
    if _MODELITO is not None and hasattr(_MODELITO, "inspect_service_state"):
        return _MODELITO.inspect_service_state(config_path)
    if _LOCAL is not None and hasattr(_LOCAL, "inspect_service_state"):
        return _LOCAL.inspect_service_state(config_path)
    raise RuntimeError("No ollama service implementation available")


def install_service(*, reinstall: bool = False) -> tuple[int, str]:
    if _MODELITO is not None and hasattr(_MODELITO, "install_service"):
        return _MODELITO.install_service(reinstall=reinstall)
    if _LOCAL is not None and hasattr(_LOCAL, "install_service"):
        return _LOCAL.install_service(reinstall=reinstall)
    return 1, "No installer available"


def start_service(config_path: Path | None = None) -> int:
    if _MODELITO is not None and hasattr(_MODELITO, "start_service"):
        return _MODELITO.start_service(config_path)
    if _LOCAL is not None and hasattr(_LOCAL, "start_service"):
        return _LOCAL.start_service(config_path)
    raise RuntimeError("No start_service implementation available")


def stop_service(config_path: Path | None = None, verbose: bool = False) -> int:
    if _MODELITO is not None and hasattr(_MODELITO, "stop_service"):
        return _MODELITO.stop_service(config_path, verbose=verbose)
    if _LOCAL is not None and hasattr(_LOCAL, "stop_service"):
        return _LOCAL.stop_service(config_path, verbose=verbose)
    raise RuntimeError("No stop_service implementation available")


def run_ollama_command(*args: str, host: str | None = None) -> subprocess.CompletedProcess:
    if _MODELITO is not None and hasattr(_MODELITO, "run_ollama_command"):
        return _MODELITO.run_ollama_command(*args, host=host)
    if _LOCAL is not None and hasattr(_LOCAL, "run_ollama_command"):
        return _LOCAL.run_ollama_command(*args, host=host)
    # Best-effort fallback: try invoking system 'ollama' directly
    cmd = ["ollama", *args]
    env = None
    if host:
        env = {**(None or {}), "OLLAMA_HOST": host}
    return subprocess.run(cmd, cwd=Path(__file__).resolve().parents[1], text=True, capture_output=True, check=False, env=env)
