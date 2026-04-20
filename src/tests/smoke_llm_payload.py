from __future__ import annotations

import json
import os
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

import pytest
import yaml

from llm import service as ollama_service

ROOT = Path(__file__).resolve().parents[2]
# Allow overriding the config used by smoke tests via env var for CI/local flexibility
CONFIG_PATH = Path(os.getenv("BATLLM_CONFIG_PATH") or str(ROOT / "src/configs/config.yaml"))
RUN_OLLAMA_SMOKE = os.getenv("BATLLM_RUN_OLLAMA_SMOKE") == "1"
DEFAULT_CHAT_TIMEOUT = 120.0

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


def _post_json(url: str, payload: dict, *, timeout: float, description: str) -> dict:
    req = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.monotonic()
    try:
        with urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except TimeoutError as exc:
        elapsed = time.monotonic() - started
        raise AssertionError(
            f"Ollama {description} timed out after {elapsed:.1f}s (timeout={timeout:.1f}s)."
        ) from exc
    except URLError as exc:
        if isinstance(exc.reason, TimeoutError):
            elapsed = time.monotonic() - started
            raise AssertionError(
                f"Ollama {description} timed out after {elapsed:.1f}s (timeout={timeout:.1f}s)."
            ) from exc
        raise


def test_ollama_health_endpoint_responds() -> None:
    llm = _load_llm_config()
    url = str(llm["url"]).rstrip("/")
    port = llm["port"]
    health_url = f"{url}:{port}/api/version"

    with urlopen(health_url, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))

    assert "version" in payload


def test_ollama_chat_returns_non_empty_content() -> None:
    llm = _load_llm_config()
    endpoint = f"{str(llm['url']).rstrip('/')}:{llm['port']}{llm['path']}"
    timeout = _resolve_chat_timeout(llm)

    payload = {
        "model": llm["model"],
        "messages": [{"role": "user", "content": "Reply with exactly OK"}],
        "stream": False,
    }
    res = _post_json(
        endpoint,
        payload,
        timeout=timeout,
        description=f"chat request for model '{llm['model']}'",
    )

    content = ""
    if isinstance(res.get("message"), dict):
        content = str(res["message"].get("content", "")).strip()
    elif isinstance(res.get("response"), str):
        content = res["response"].strip()

    assert content != ""
