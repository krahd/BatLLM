from __future__ import annotations

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


def test_invoke_with_timeout_guard_reports_timeout_with_context(monkeypatch) -> None:
    times = iter((100.0, 161.0))

    def fake_monotonic() -> float:
        return next(times)

    def fake_invoke():
        raise TimeoutError("timed out")

    monkeypatch.setattr(smoke_llm_payload.time, "monotonic", fake_monotonic)

    with pytest.raises(AssertionError) as exc_info:
        smoke_llm_payload._invoke_with_timeout_guard(
            fake_invoke,
            timeout=60.0,
            description="chat request for model 'qwen3:30b'",
        )

    message = str(exc_info.value)
    assert "chat request for model 'qwen3:30b'" in message
    assert "timeout=60.0s" in message


def test_invoke_with_timeout_guard_preserves_non_timeout_errors() -> None:
    def fake_invoke():
        raise RuntimeError("connection refused")

    with pytest.raises(RuntimeError, match="connection refused"):
        smoke_llm_payload._invoke_with_timeout_guard(
            fake_invoke,
            timeout=60.0,
            description="chat request",
        )


def test_summarize_once_uses_provider_and_timeout(monkeypatch) -> None:
    calls = {}

    class FakeProvider:
        def __init__(self, host: str, port: int, model: str):
            calls["init"] = {"host": host, "port": port, "model": model}

        def summarize(self, messages, settings=None):
            calls["message"] = messages[0].content
            calls["settings"] = settings
            return "OK"

    monkeypatch.setattr(smoke_llm_payload, "OllamaProvider", FakeProvider)
    monkeypatch.setattr(smoke_llm_payload, "_resolve_chat_timeout", lambda _llm: 88.0)

    result = smoke_llm_payload._summarize_once(
        {"url": "http://localhost", "port": 11434, "model": "qwen3:30b"},
        "Reply with exactly OK",
    )

    assert result == "OK"
    assert calls["init"] == {
        "host": "http://localhost",
        "port": 11434,
        "model": "qwen3:30b",
    }
    assert calls["message"] == "Reply with exactly OK"
    assert calls["settings"] == {"timeout": 88.0}


def test_version_endpoint_responds_uses_configured_url(monkeypatch) -> None:
    calls = {}

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    def fake_urlopen(url, timeout):
        calls["url"] = url
        calls["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(smoke_llm_payload, "urlopen", fake_urlopen)

    assert smoke_llm_payload._version_endpoint_responds(
        {"url": "http://127.0.0.1/", "port": 11434}
    )
    assert calls == {"url": "http://127.0.0.1:11434/api/version", "timeout": 5.0}
