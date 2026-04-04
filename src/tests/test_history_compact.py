from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "src/configs/config.yaml"
START_SCRIPT = ROOT / "start_ollama.sh"
STOP_SCRIPT = ROOT / "stop_ollama.sh"


def _bash_syntax_command() -> list[str]:
    """Return a shell parser command that works on the current platform."""
    if os.name != "nt":
        return ["bash", "-n"]

    candidates = [
        Path(r"C:\Program Files\Git\bin\bash.exe"),
        Path(r"C:\Program Files\Git\usr\bin\bash.exe"),
    ]
    discovered = shutil.which("bash")
    if discovered:
        candidates.append(Path(discovered))

    for candidate in candidates:
        if not candidate.exists():
            continue
        if "system32" in str(candidate).lower():
            continue
        return [str(candidate), "-n"]

    pytest.skip("No usable bash executable is available on Windows.")


def test_llm_config_has_required_fields() -> None:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    llm = config.get("llm") or {}

    missing = [
        key
        for key in ("model", "url", "port", "path")
        if llm.get(key) in (None, "")
    ]

    assert not missing, f"Missing llm config keys: {missing}"


def test_ollama_scripts_have_valid_shell_syntax() -> None:
    command = _bash_syntax_command()
    for script in (START_SCRIPT, STOP_SCRIPT):
        proc = subprocess.run(
            [*command, str(script)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, f"{script.name} failed shell parse: {proc.stderr or proc.stdout}"


def test_source_tree_compiles() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "compileall", "-q", str(ROOT / "src")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
