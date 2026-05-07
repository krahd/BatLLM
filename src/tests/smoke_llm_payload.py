from __future__ import annotations

import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

import pytest
import yaml

from llm import service as ollama_service
from modelito import Message, OllamaProvider
from modelito import ollama_service as modelito_ollama_service

ROOT = Path(__file__).resolve().parents[2]
# Allow overriding the config used by smoke tests via env var for CI/local flexibility
CONFIG_PATH = Path(os.getenv("BATLLM_CONFIG_PATH") or str(ROOT / "src/configs/config.yaml"))
RUN_OLLAMA_SMOKE = os.getenv("BATLLM_RUN_OLLAMA_SMOKE") == "1"
DEFAULT_CHAT_TIMEOUT = 120.0
ResultT = TypeVar("ResultT")

pytestmark = pytest.mark.skipif(
    not RUN_OLLAMA_SMOKE,
    reason="Set BATLLM_RUN_OLLAMA_SMOKE=1 to run live Ollama smoke tests.",
)


def _load_llm_config() -> dict:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    return config.get("llm") or {}


def _resolve_chat_timeout(llm: dict) -> float:
    return ollama_service.resolve_request_timeout(
        llm,
        default=DEFAULT_CHAT_TIMEOUT,
        model=str(llm.get("model") or "").strip() or None,
    )


def _invoke_with_timeout_guard(
    invoke: Callable[[], ResultT], *, timeout: float, description: str
) -> ResultT:
    started = time.monotonic()
    try:
        return invoke()
    except TimeoutError as exc:
        elapsed = time.monotonic() - started
        raise AssertionError(
            f"Ollama {description} timed out after {elapsed:.1f}s (timeout={timeout:.1f}s)."
        ) from exc


def _summarize_once(llm: dict, prompt: str) -> str:
    timeout = _resolve_chat_timeout(llm)
    provider = OllamaProvider(
        host=str(llm["url"]).rstrip("/"),
        port=int(llm["port"]),
        model=str(llm["model"]),
    )
    return _invoke_with_timeout_guard(
        lambda: provider.summarize(
            [Message(role="user", content=prompt)],
            settings={"timeout": timeout},
        ),
        timeout=timeout,
        description=f"chat request for model '{llm['model']}'",
    )


def test_ollama_health_endpoint_responds() -> None:
    state = modelito_ollama_service.inspect_service_state(str(CONFIG_PATH))

    assert state.get("running") is True
    assert state.get("version")


def test_ollama_chat_returns_non_empty_content() -> None:
    llm = _load_llm_config()
    content = _summarize_once(llm, "Reply with exactly OK").strip()

    assert content != ""
