"""Regression coverage for the urgent findings of the 10 November 2026 audit."""
from __future__ import annotations

from importlib import import_module
import os
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace

import pytest

from configs.app_config import SHIPPED_CONFIG_PATH, AppConfig, config, load_config_data
from game.ollama_connector import OllamaConnector
from game.prompt_store import PromptStore
from game.replay_engine import parse_model_response
from view.home_screen import HomeScreen


ROOT = Path(__file__).resolve().parents[2]
INSTRUCTIONS_DIR = ROOT / "src/assets/system_instructions"
AUGMENTED_FILES = ("augmented_independent_1.txt", "augmented_shared_1.txt")
SECTION_LABELS = {"[GAME_STATE]", "[PLAYER_INPUT]"}


# --- prompt-history retrieve button -------------------------------------------------

def _home_screen_with_store(prompt_store: PromptStore, draft: str) -> HomeScreen:
    screen = HomeScreen()
    screen.ids = {
        "prompt_input_1": SimpleNamespace(text=draft),
        "prompt_store_viewer_1": SimpleNamespace(text=""),
        "game_board": SimpleNamespace(prompt_store=prompt_store),
    }
    return screen


def test_retrieve_without_submitted_prompt_keeps_draft_and_never_assigns_none() -> None:
    screen = _home_screen_with_store(PromptStore(), "unsent draft")

    screen.retrieve_prompt_history_selected_text(1)

    assert screen.ids["prompt_input_1"].text == "unsent draft"


def test_retrieve_after_store_reset_keeps_draft() -> None:
    store = PromptStore()
    store.add_prompt(1, "first")
    store.reset()
    screen = _home_screen_with_store(store, "new game draft")

    screen.retrieve_prompt_history_selected_text(1)

    assert screen.ids["prompt_input_1"].text == "new game draft"


def test_retrieve_copies_selected_prompt_into_editor() -> None:
    store = PromptStore()
    store.add_prompt(1, "first")
    store.add_prompt(1, "second")
    store.rewind(1)
    screen = _home_screen_with_store(store, "")

    screen.retrieve_prompt_history_selected_text(1)

    assert screen.ids["prompt_input_1"].text == "first"


# --- configurator first run ---------------------------------------------------------

@pytest.fixture
def editor(monkeypatch):
    # The editor sets minimum window dimensions at import time.
    monkeypatch.setattr("kivy.core.window.Window", SimpleNamespace(), raising=False)
    return import_module("configs.configurator")


def test_configurator_first_run_does_not_write_a_user_config(editor, tmp_path) -> None:
    target = tmp_path / "fresh-home" / "config.yaml"

    editor.BatLLMConfigApp._ensure_config_file(None, str(target))

    assert not target.exists()
    assert target.parent.is_dir()


def test_configurator_first_run_preserves_shipped_defaults(editor, tmp_path) -> None:
    target = tmp_path / "fresh-home" / "config.yaml"
    shipped = load_config_data(SHIPPED_CONFIG_PATH)["llm"]

    editor.BatLLMConfigApp._ensure_config_file(None, str(target))
    loaded = editor.ConfigManager(str(target)).load()["llm"]
    effective = AppConfig(path=target)

    for key in ("model", "timeout", "num_ctx", "url", "port"):
        assert loaded[key] == shipped[key], key
        assert effective.get("llm", key) == shipped[key], key
    assert loaded["model"] == "smollm2"
    assert loaded["num_ctx"] == 4096


def test_configurator_ensure_keeps_an_existing_user_config(editor, tmp_path) -> None:
    target = tmp_path / "config.yaml"
    target.write_text("llm:\n  model: qwen3:8b\n", encoding="utf-8")

    editor.BatLLMConfigApp._ensure_config_file(None, str(target))

    assert target.read_text(encoding="utf-8") == "llm:\n  model: qwen3:8b\n"
    assert editor.ConfigManager(str(target)).load()["llm"]["model"] == "qwen3:8b"


# --- system-instruction placeholders ------------------------------------------------

def _connector(monkeypatch, *, independent: bool) -> OllamaConnector:
    monkeypatch.setattr("game.ollama_connector.Client", lambda *args, **kwargs: object())
    config.set_temporary("game", "prompt_augmentation", True)
    config.set_temporary("game", "independent_contexts", independent)
    connector = OllamaConnector()
    connector.augmenting_prompt = True
    connector.independent_contexts = independent
    return connector


@pytest.mark.parametrize("independent", [True, False])
def test_augmented_instructions_substitute_rule_placeholders(monkeypatch, independent) -> None:
    config.set_temporary("game", "bullet_damage", 7)
    config.set_temporary("game", "bot_step_length", 0.045)
    connector = _connector(monkeypatch, independent=independent)

    text = connector._get_system_instructions_text()

    assert "[BULLET_DAMAGE]" not in text
    assert "[STEP_LENGTH]" not in text
    assert "its health decreases by 7." in text
    assert "moves forward a distance of 0.045." in text
    # Only the literal section labels used by augmented prompts remain bracketed.
    assert set(re.findall(r"\[[A-Z_]+\]", text)) == SECTION_LABELS


def test_request_sends_rendered_system_instructions(monkeypatch) -> None:
    config.set_temporary("game", "bullet_damage", 9)
    connector = _connector(monkeypatch, independent=True)
    calls = []
    connector.client = SimpleNamespace(
        chat=lambda **kwargs: calls.append(kwargs) or {"message": {"content": "M"}}
    )

    connector.send_prompt_to_llm_sync(1, user_text="advance", game_state={})

    system = calls[-1]["messages"][0]
    assert system["role"] == "system"
    assert "its health decreases by 9." in system["content"]
    assert "[BULLET_DAMAGE]" not in system["content"]


@pytest.mark.parametrize("filename", AUGMENTED_FILES)
def test_instruction_examples_are_valid_commands(filename) -> None:
    text = (INSTRUCTIONS_DIR / filename).read_text(encoding="utf-8")
    examples = re.findall(r"Example: (\S+)", text)

    assert len(examples) >= 8
    for example in examples:
        parsed = parse_model_response(example)
        assert parsed.valid, f"{filename}: example {example!r} does not parse"


@pytest.mark.parametrize("filename", AUGMENTED_FILES)
def test_instructions_document_every_command_form(filename) -> None:
    text = (INSTRUCTIONS_DIR / filename).read_text(encoding="utf-8")

    for form in ("C{angle}", "A{angle}", "M ", "M{distance}", "S1 ", "S0 ", "S ", "B "):
        assert re.search(rf"^\s+{re.escape(form)}", text, flags=re.MULTILINE), form


# --- Ollama shell scripts -----------------------------------------------------------

pytestmark_posix = pytest.mark.skipif(os.name == "nt", reason="POSIX shell scripts")


def _script_env(**overrides: str) -> dict[str, str]:
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env.update(overrides)
    return env


@pytestmark_posix
@pytest.mark.parametrize("action", ["start", "stop"])
def test_ollama_script_resolves_module_from_any_directory(action, tmp_path) -> None:
    """Run the real script and module up to argument parsing; no service is touched."""
    proc = subprocess.run(
        ["bash", str(ROOT / f"{action}_ollama.sh"), "--help"],
        cwd=tmp_path,
        env=_script_env(BATLLM_PYTHON=sys.executable),
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "No module named" not in proc.stderr
    assert "usage:" in proc.stdout


@pytestmark_posix
@pytest.mark.parametrize("action", ["start", "stop"])
def test_ollama_script_passes_action_arguments_and_source_path(action, tmp_path) -> None:
    recorder = tmp_path / "fake-python"
    recorder.write_text(
        '#!/usr/bin/env bash\nprintf "%s\\n" "PYTHONPATH=$PYTHONPATH" "$@"\n',
        encoding="utf-8",
    )
    recorder.chmod(0o755)

    proc = subprocess.run(
        ["bash", str(ROOT / f"{action}_ollama.sh"), "--extra", "value with space"],
        cwd=tmp_path,
        env=_script_env(BATLLM_PYTHON=str(recorder), PYTHONPATH="/existing/path"),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.splitlines() == [
        f"PYTHONPATH={ROOT / 'src'}:/existing/path",
        "-m",
        "llm.service",
        action,
        "--extra",
        "value with space",
    ]
