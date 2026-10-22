"""Minimal strict Ollama chat client for LXAI experiments.

The experimental runners use this adapter instead of Modelito so the exact
Ollama `/api/chat` request is controlled and provider options are not silently
ignored. There is no CLI or deterministic fallback: transport failures surface
as experiment provider errors.
"""
from __future__ import annotations

import json
from typing import Any
from urllib.request import Request, urlopen


class DirectOllamaChatClient:
    """Send exact stateless chat requests to a local Ollama server."""

    def __init__(self, *, host: str = "http://localhost", port: int = 11434, timeout: float = 120.0):
        clean = str(host).rstrip("/")
        suffix = f":{int(port)}"
        self.base_url = clean if clean.endswith(suffix) else clean + suffix
        self.timeout = float(timeout)

    def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        options: dict[str, Any],
        stream: bool = False,
    ) -> dict[str, Any]:
        if stream:
            raise ValueError("LXAI experiments require stream=False.")
        payload = {
            "model": str(model),
            "messages": [
                {"role": str(message["role"]), "content": str(message["content"])}
                for message in messages
            ],
            "stream": False,
            "options": dict(options),
        }
        request = Request(
            self.base_url + "/api/chat",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=self.timeout) as response:  # nosec B310 - local configured endpoint
            result = json.loads(response.read().decode("utf-8"))
        if not isinstance(result, dict):
            raise RuntimeError(f"Unexpected Ollama response type: {type(result).__name__}")
        message = result.get("message")
        if not isinstance(message, dict) or not str(message.get("content") or "").strip():
            raise RuntimeError(f"Ollama response missing message.content: {result!r}")
        return result
