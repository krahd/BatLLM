"""Canonical trace and integrity helpers for BatLLM research sessions.

The trace contract deliberately separates model-invocation provenance from
replayable game transitions. Model outputs are recorded, not assumed to be
regenerable. Grounded commands are replayed against frozen game rules.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

TRACE_SCHEMA_VERSION = 3
TRACE_SESSION_TYPE = "batllm_research_session"
REDACTED_TEXT = "[REDACTED]"


class PrivacyMode(str, Enum):
    """Content-retention policy for prompt and model text."""

    FULL = "full"
    REDACTED = "redacted"
    HASHED = "hashed"


def utc_now_iso() -> str:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    """Create a stable-format opaque identifier."""

    return f"{prefix}_{uuid4().hex}"


def _normalise(value: Any) -> Any:
    """Convert supported Python values into canonical JSON-compatible values."""

    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _normalise(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalise(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Canonical traces do not permit NaN or infinite floats.")
        return 0.0 if value == 0 else value
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise TypeError(f"Unsupported canonical value: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    """Serialise a value deterministically for hashing and comparison."""

    return json.dumps(
        _normalise(value),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_bytes(data: bytes) -> str:
    """Return the lowercase SHA-256 digest of bytes."""

    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    """Return the lowercase SHA-256 digest of UTF-8 text."""

    return sha256_bytes(text.encode("utf-8"))


def sha256_json(value: Any) -> str:
    """Return the digest of a value's canonical JSON representation."""

    return sha256_text(canonical_json(value))


def protect_text(value: str | None, mode: PrivacyMode | str) -> dict[str, Any]:
    """Return a content object with a commitment and optional retained text."""

    privacy = PrivacyMode(mode)
    text = "" if value is None else str(value)
    protected: dict[str, Any] = {
        "sha256": sha256_text(text),
        "length": len(text),
        "encoding": "utf-8",
    }
    if privacy is PrivacyMode.FULL:
        protected["text"] = text
    elif privacy is PrivacyMode.REDACTED:
        protected["text"] = REDACTED_TEXT
    return protected


def protected_text_mode(value: Mapping[str, Any]) -> PrivacyMode:
    """Infer the retention mode represented by a protected-text object."""

    if "text" not in value:
        return PrivacyMode.HASHED
    if value.get("text") == REDACTED_TEXT:
        return PrivacyMode.REDACTED
    return PrivacyMode.FULL


def verify_protected_text(value: Mapping[str, Any]) -> bool:
    """Verify retained full text; privacy-reduced records remain commitments."""

    text = value.get("text")
    if text is None or text == REDACTED_TEXT:
        return True
    rendered = str(text)
    return (
        value.get("sha256") == sha256_text(rendered)
        and value.get("length") == len(rendered)
        and value.get("encoding") == "utf-8"
    )


def _redact_message(message: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(message))
    if "content" in result:
        content = result.get("content")
        result["content"] = {
            "redacted": True,
            "canonical_sha256": sha256_json(content),
            "original_type": type(content).__name__,
        }
    return result


def store_request_payload(
    payload: Mapping[str, Any], mode: PrivacyMode | str
) -> dict[str, Any]:
    """Store a request according to privacy mode while retaining commitments."""

    privacy = PrivacyMode(mode)
    exact = _normalise(payload)
    record: dict[str, Any] = {
        "privacy_mode": privacy.value,
        "canonical_sha256": sha256_json(exact),
    }

    if privacy is PrivacyMode.FULL:
        stored = exact
    elif privacy is PrivacyMode.REDACTED:
        stored = deepcopy(exact)
        if isinstance(stored, dict) and isinstance(stored.get("messages"), list):
            stored["messages"] = [
                _redact_message(message) if isinstance(message, Mapping) else message
                for message in stored["messages"]
            ]
    else:
        stored = None

    if stored is not None:
        record["payload"] = stored
        record["stored_sha256"] = sha256_json(stored)
    return record


def _verify_redacted_messages(payload: Mapping[str, Any]) -> bool:
    messages = payload.get("messages")
    if not isinstance(messages, list):
        return False
    for message in messages:
        if not isinstance(message, Mapping):
            return False
        content = message.get("content")
        if not isinstance(content, Mapping):
            return False
        if content.get("redacted") is not True:
            return False
        digest = content.get("canonical_sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            return False
    return True


def verify_request_record(record: Mapping[str, Any]) -> tuple[bool, str]:
    """Verify request storage and report the strongest available guarantee."""

    try:
        mode = PrivacyMode(record.get("privacy_mode", PrivacyMode.HASHED.value))
    except ValueError:
        return False, "invalid-privacy-mode"
    payload = record.get("payload")
    if mode is PrivacyMode.HASHED:
        return bool(record.get("canonical_sha256")), "commitment-only"
    if not isinstance(payload, Mapping):
        return False, "missing-payload"
    if record.get("stored_sha256") != sha256_json(payload):
        return False, "stored-payload-hash-mismatch"
    if mode is PrivacyMode.FULL:
        if record.get("canonical_sha256") != sha256_json(payload):
            return False, "canonical-request-hash-mismatch"
        return True, "exact-reconstruction"
    if not _verify_redacted_messages(payload):
        return False, "malformed-redacted-request"
    return True, "redacted-structure"


def event_to_dict(event: Any) -> dict[str, Any]:
    """Convert replay-engine events to ordinary dictionaries."""

    if is_dataclass(event):
        return _normalise(asdict(event))
    if isinstance(event, Mapping):
        return _normalise(event)
    return {"type": type(event).__name__, "label": str(event)}


def transition_material(
    *,
    bot_id: int,
    pre_state: Mapping[Any, Any],
    command: str,
    rules: Mapping[str, Any],
    post_state: Mapping[Any, Any],
    events: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return the canonical material committed by a transition hash."""

    return {
        "bot_id": int(bot_id),
        "pre_state": _normalise(pre_state),
        "command": str(command),
        "rules": _normalise(rules),
        "post_state": _normalise(post_state),
        "events": _normalise(events or []),
    }


def transition_hash(**kwargs: Any) -> str:
    """Return the canonical transition commitment."""

    return sha256_json(transition_material(**kwargs))


def finalise_play_hash(
    play: Mapping[str, Any], previous_play_sha256: str | None
) -> dict[str, Any]:
    """Attach ordered-chain and content commitments to a play record."""

    result = deepcopy(dict(play))
    result.pop("play_sha256", None)
    result.pop("chain_sha256", None)
    result["previous_play_sha256"] = previous_play_sha256
    content_hash = sha256_json(result)
    result["play_sha256"] = content_hash
    result["chain_sha256"] = sha256_json(
        {"previous": previous_play_sha256, "play": content_hash}
    )
    return result


def verify_play_hashes(
    play: Mapping[str, Any], expected_previous: str | None
) -> tuple[bool, list[str]]:
    """Verify content and ordered-chain hashes for one play."""

    errors: list[str] = []
    if play.get("previous_play_sha256") != expected_previous:
        errors.append("previous-play-hash-mismatch")
    material = deepcopy(dict(play))
    recorded_play_hash = material.pop("play_sha256", None)
    recorded_chain_hash = material.pop("chain_sha256", None)
    expected_play_hash = sha256_json(material)
    if recorded_play_hash != expected_play_hash:
        errors.append("play-hash-mismatch")
    expected_chain_hash = sha256_json(
        {"previous": expected_previous, "play": expected_play_hash}
    )
    if recorded_chain_hash != expected_chain_hash:
        errors.append("chain-hash-mismatch")
    return not errors, errors
