from __future__ import annotations

from urllib.error import URLError

import pytest

from tests import smoke_llm_payload


def test_resolve_chat_timeout_uses_positive_configured_value() -> None:
    assert smoke_llm_payload._resolve_chat_timeout({"timeout": 75}) == 75.0
    assert smoke_llm_payload._resolve_chat_timeout({"timeout": "90"}) == 90.0


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
