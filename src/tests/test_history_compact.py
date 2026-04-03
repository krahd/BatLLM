from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "src/configs/config.yaml"
START_SCRIPT = ROOT / "start_ollama.sh"
STOP_SCRIPT = ROOT / "stop_ollama.sh"


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
    for script in (START_SCRIPT, STOP_SCRIPT):
        proc = subprocess.run(
            ["bash", "-n", str(script)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, f"{script.name} failed shell parse: {proc.stderr}"


def test_source_tree_compiles() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "compileall", "-q", str(ROOT / "src")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
