from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "src/configs/config.yaml"
RUN_OLLAMA_SMOKE = os.getenv("BATLLM_RUN_OLLAMA_SMOKE") == "1"

pytestmark = pytest.mark.skipif(
    not RUN_OLLAMA_SMOKE,
    reason="Set BATLLM_RUN_OLLAMA_SMOKE=1 to run live Ollama smoke tests.",
)


def _load_llm_config() -> dict:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    return config.get("llm") or {}


def _post_json(url: str, payload: dict) -> dict:
    req = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=60) as response:
        body = response.read().decode("utf-8")
        return json.loads(body) if body else {}


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

    payload = {
        "model": llm["model"],
        "messages": [{"role": "user", "content": "Reply with exactly OK"}],
        "stream": False,
    }
    res = _post_json(endpoint, payload)

    content = ""
    if isinstance(res.get("message"), dict):
        content = str(res["message"].get("content", "")).strip()
    elif isinstance(res.get("response"), str):
        content = res["response"].strip()

    assert content != ""
