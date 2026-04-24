from __future__ import annotations

from urllib.error import URLError

import pytest

from tests import smoke_llm_payload


def test_resolve_chat_timeout_uses_positive_configured_value() -> None:
    assert smoke_llm_payload._resolve_chat_timeout({"timeout": 75}) == 75.0
    assert smoke_llm_payload._resolve_chat_timeout({"timeout": "90"}) == 90.0


def test_resolve_chat_timeout_prefers_model_override() -> None:
    assert smoke_llm_payload._resolve_chat_timeout(
        {
            "model": "qwen3:30b",
            "timeout": 60,
            "model_timeouts": {"qwen3:30b": 180},
        }
    ) == 180.0


def test_resolve_chat_timeout_uses_common_model_default() -> None:
    assert smoke_llm_payload._resolve_chat_timeout(
        {
            "model": "llama3.2:latest",
            "timeout": None,
            "model_timeouts": {},
        }
    ) == 75.0


def test_resolve_chat_timeout_falls_back_to_default() -> None:
    assert smoke_llm_payload._resolve_chat_timeout({"timeout": None}) == 120.0
    assert smoke_llm_payload._resolve_chat_timeout({"timeout": 0}) == 120.0
    assert smoke_llm_payload._resolve_chat_timeout({"timeout": "invalid"}) == 120.0


def test_post_json_reports_timeout_with_context(monkeypatch) -> None:
    times = iter((100.0, 161.0))

    def fake_monotonic() -> float:
        return next(times)

    def fake_urlopen(*_args, **_kwargs):
        raise URLError(TimeoutError("timed out"))

    monkeypatch.setattr(smoke_llm_payload.time, "monotonic", fake_monotonic)
    monkeypatch.setattr(smoke_llm_payload, "urlopen", fake_urlopen)

    with pytest.raises(AssertionError) as exc_info:
        smoke_llm_payload._post_json(
            "http://localhost:11434/api/chat",
            {"model": "qwen3:30b"},
            timeout=60.0,
            description="chat request for model 'qwen3:30b'",
        )

    message = str(exc_info.value)
    assert "chat request for model 'qwen3:30b'" in message
    assert "timeout=60.0s" in message


def test_post_json_raises_for_non_timeout_url_errors(monkeypatch) -> None:
    def fake_urlopen(*_args, **_kwargs):
        raise URLError("connection refused")

    monkeypatch.setattr(smoke_llm_payload, "urlopen", fake_urlopen)

    with pytest.raises(URLError, match="connection refused"):
        smoke_llm_payload._post_json(
            "http://localhost:11434/api/chat",
            {"model": "qwen3:30b"},
            timeout=60.0,
            description="chat request",
        )


def test_post_json_raises_for_malformed_json_payload(monkeypatch) -> None:
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b"{not-json"

    monkeypatch.setattr(smoke_llm_payload, "urlopen", lambda *_args, **_kwargs: FakeResponse())

    with pytest.raises(ValueError):
        smoke_llm_payload._post_json(
            "http://localhost:11434/api/chat",
            {"model": "qwen3:30b"},
            timeout=60.0,
            description="chat request",
        )
