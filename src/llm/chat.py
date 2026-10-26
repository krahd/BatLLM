"""Shared strict Ollama transport for gameplay and research.

Modelito 1.4.6 preserves native roles/options and disables inference fallbacks.
Request deadlines are provider attributes, not generation settings.
"""
from __future__ import annotations

import math
from urllib.parse import urlsplit

from modelito import Message, OllamaProvider


class Client:
    """Small dictionary-response adapter used by both application runtimes."""

    def __init__(self, host: str, timeout: float | None = None):
        self.host = host.rstrip("/")
        self.timeout = 120.0 if timeout is None else float(timeout)

    def _prepare(self, model, messages, options):
        settings = dict(options or {})
        timeout = float(settings.pop("timeout", self.timeout))
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("Request timeout must be finite and positive")
        parsed = urlsplit(self.host if "://" in self.host else f"http://{self.host}")
        hostname = parsed.hostname or "localhost"
        if ":" in hostname:
            hostname = f"[{hostname}]"
        provider = OllamaProvider(
            host=f"{parsed.scheme}://{hostname}", port=parsed.port or 11434,
            model=model, timeout=timeout, strict=True,
        )
        converted = [Message(role=m["role"], content=m["content"]) for m in messages]
        return provider, converted, settings

    def stream_text(self, *, model, messages, options=None):
        """Yield strict native fragments; close the provider iterator on cancellation."""
        provider, converted, settings = self._prepare(model, messages, options)
        yield from provider.stream(converted, settings=settings)

    def chat(self, *, model, messages, options=None, stream=False):
        """Return generated text; transport and provider errors always propagate."""
        if stream:
            text = "".join(self.stream_text(model=model, messages=messages, options=options))
        else:
            provider, converted, settings = self._prepare(model, messages, options)
            text = provider.summarize(converted, settings=settings)
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Ollama returned no textual completion")
        return {"message": {"content": text}, "response": text}
