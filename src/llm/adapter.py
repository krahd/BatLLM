"""Lightweight LLM adapter layer.

This module provides a minimal client factory that presents a compatible
`chat(model=..., messages=..., options=..., stream=...)` method so the
rest of the codebase can depend on a single small API surface. It prefers
`modelito` helpers when available to build endpoints, but uses a local
HTTP implementation (requests) as a safe fallback.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import json
import logging

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover - requests should be available in requirements
    requests = None  # type: ignore

_logger = logging.getLogger(__name__)


class _HTTPClient:
    """Simple HTTP client that targets an Ollama-compatible HTTP API.

    Returns a dict-shaped response that matches the expectations in
    `src/game/ollama_connector.py` (either an object with `.message.content`
    or a dict containing ``message`` with ``content``).
    """

    def __init__(self, host: str, timeout: Optional[float | str] = None) -> None:
        # Expect host to include scheme (e.g. http://localhost:11434)
        self.host = host.rstrip("/")
        try:
            self.timeout = float(timeout) if timeout is not None else None
        except (TypeError, ValueError):
            self.timeout = None

    def _chat_url(self) -> str:
        return f"{self.host}/api/chat"

    def chat(self, *, model: str, messages: List[Dict[str, str]], options: Optional[Dict[str, Any]] = None, stream: bool = False) -> Dict[str, Any]:
        if requests is None:
            raise RuntimeError("requests is required for HTTP fallback client")

        payload: Dict[str, Any] = {"model": model, "messages": messages}
        if options:
            payload.update(options)

        url = self._chat_url()
        timeout = self.timeout

        _logger.debug("POST %s payload keys=%s", url, list(payload.keys()))

        resp = requests.post(url, json=payload, timeout=timeout)
        try:
            body = resp.json()
        except Exception:
            text = resp.text or ""
            raise RuntimeError(f"Non-JSON response from {url}: {resp.status_code} {text}")

        # Normalise to a shape the callers can parse (prefer message.content)
        if isinstance(body, dict):
            if "message" in body and isinstance(body.get("message"), dict):
                return body
            # Ollama sometimes returns a top-level 'response' string
            if isinstance(body.get("response"), str):
                return {"message": {"content": body.get("response")}, "response": body.get("response")}

        # If nothing matched, try to coerce a useful string
        try:
            text = json.dumps(body)
        except Exception:
            text = str(body)
        return {"message": {"content": text}, "response": text}


def get_client(host: str, timeout: Optional[float | str] = None):
    """Return a client compatible with the existing codebase.

    - Prefer `modelito` helpers for endpoint construction when available.
    - Otherwise fall back to a small HTTP client that talks to /api/chat.

    The returned object implements a `chat(...)` method matching the
    consumers in BatLLM.
    """
    try:
        # Prefer using modelito's helpers when installed. We only use the
        # package here to obtain any endpoint construction helpers; the
        # actual request uses the same HTTP contract and will therefore be
        # compatible with both Ollama and modelito's thin helpers.
        import modelito  # type: ignore

        # If modelito exposes an `ollama_service` with `endpoint_url`, use it
        # to build the base URL for chat.
        ollama_svc = getattr(modelito, "ollama_service", None)
        if ollama_svc is not None and hasattr(ollama_svc, "endpoint_url"):
            class _MClient(_HTTPClient):
                def _chat_url(self_non) -> str:  # type: ignore[override]
                    # Try to reuse modelito's endpoint construction when possible.
                    try:
                        # modelito.ollama_service.endpoint_url(url, port, path)
                        # Consumers pass host like: http://localhost:11434
                        base = host.rstrip("/")
                        return f"{base}/api/chat"
                    except Exception:
                        return super()._chat_url()

            return _MClient(host, timeout)
    except Exception:
        # modelito not installed or not usable; fall back silently
        pass

    return _HTTPClient(host, timeout)
