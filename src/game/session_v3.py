"""BatLLM research-session schema-v3 builders and semantic validation."""
# pylint: disable=too-many-branches,too-many-statements,too-many-locals

from __future__ import annotations

from copy import deepcopy
from importlib import metadata
import json
import platform
from pathlib import Path
import re
import sys
from typing import Any, Mapping

from game.trace_contract import (
    PrivacyMode,
    TRACE_SCHEMA_VERSION,
    TRACE_SESSION_TYPE,
    new_id,
    sha256_json,
    utc_now_iso,
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class SessionV3Error(ValueError):
    """Raised when a research session violates schema-v3 invariants."""


def runtime_provenance(extra: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Capture the execution environment needed to interpret a trace."""

    packages: dict[str, str] = {}
    for package in ("BatLLM", "modelito", "ollama", "kivy", "kivymd"):
        try:
            packages[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            continue
    provenance: dict[str, Any] = {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "byteorder": sys.byteorder,
        "dependency_versions": packages,
    }
    if extra:
        provenance.update(dict(extra))
    return provenance


def application_provenance(
    *, app_version: str, git_commit: str | None = None
) -> dict[str, Any]:
    return {
        "name": "BatLLM",
        "version": str(app_version),
        "git_commit": git_commit,
        "trace_schema_version": TRACE_SCHEMA_VERSION,
    }


def build_session_v3(
    *,
    games: list[dict[str, Any]],
    app_version: str,
    privacy_mode: PrivacyMode | str = PrivacyMode.FULL,
    git_commit: str | None = None,
    model_provenance: Mapping[str, Any] | None = None,
    runtime: Mapping[str, Any] | None = None,
    session_id: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Build a schema-v3 envelope and commit to its complete contents."""

    payload: dict[str, Any] = {
        "schema_version": TRACE_SCHEMA_VERSION,
        "session_type": TRACE_SESSION_TYPE,
        "session_id": session_id or new_id("session"),
        "created_at": created_at or utc_now_iso(),
        "privacy_mode": PrivacyMode(privacy_mode).value,
        "application_provenance": application_provenance(
            app_version=app_version, git_commit=git_commit
        ),
        "runtime_provenance": runtime_provenance(runtime),
        "model_provenance": dict(model_provenance or {}),
        "games": deepcopy(games),
    }
    payload["session_sha256"] = sha256_json(payload)
    return payload


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SessionV3Error(message)


def _require_sha(value: Any, label: str, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    _require(
        isinstance(value, str) and bool(_SHA256_RE.fullmatch(value)),
        f"{label} must be a lowercase SHA-256 digest.",
    )


def _validate_protected_text(value: Any, label: str) -> None:
    _require(isinstance(value, dict), f"{label} must be an object.")
    _require_sha(value.get("sha256"), f"{label}.sha256")
    _require(
        isinstance(value.get("length"), int) and value["length"] >= 0,
        f"{label}.length must be a non-negative integer.",
    )
    _require(value.get("encoding") == "utf-8", f"{label}.encoding must be utf-8.")
    if "text" in value:
        _require(isinstance(value["text"], str), f"{label}.text must be a string.")


def _require_content_mode(
    value: Mapping[str, Any], expected: PrivacyMode, label: str
) -> None:
    if expected is PrivacyMode.FULL:
        _require(
            "text" in value and isinstance(value.get("text"), str),
            f"{label} must retain full text.",
        )
    elif expected is PrivacyMode.REDACTED:
        _require(
            value.get("text") == "[REDACTED]",
            f"{label} must contain the redaction marker.",
        )
    else:
        _require(
            "text" not in value,
            f"{label} must not retain text in hash-only mode.",
        )


def validate_session_v3(payload: Any) -> dict[str, Any]:
    """Perform structural checks before the verifier evaluates semantics."""

    _require(isinstance(payload, dict), "Session must be a JSON object.")
    _require(
        payload.get("schema_version") == TRACE_SCHEMA_VERSION,
        f"schema_version must be {TRACE_SCHEMA_VERSION}.",
    )
    _require(
        payload.get("session_type") == TRACE_SESSION_TYPE,
        f"session_type must be {TRACE_SESSION_TYPE!r}.",
    )
    _require(
        isinstance(payload.get("session_id"), str) and bool(payload["session_id"]),
        "session_id is required.",
    )
    _require(isinstance(payload.get("created_at"), str), "created_at is required.")
    _require(
        payload.get("privacy_mode") in {mode.value for mode in PrivacyMode},
        "privacy_mode is invalid.",
    )
    privacy = PrivacyMode(payload["privacy_mode"])
    for key in (
        "application_provenance",
        "runtime_provenance",
        "model_provenance",
    ):
        _require(isinstance(payload.get(key), dict), f"{key} must be an object.")
    _require_sha(payload.get("session_sha256"), "session_sha256")

    games = payload.get("games")
    _require(isinstance(games, list) and bool(games), "games must be a non-empty list.")

    seen_play_ids: set[str] = set()
    seen_sequences: set[int] = set()
    for game_index, game in enumerate(games, start=1):
        _require(isinstance(game, dict), f"Game {game_index} must be an object.")
        _require(isinstance(game.get("final_state"), dict), f"Game {game_index} lacks final_state.")
        _require(
            isinstance(game.get("rounds"), list) and bool(game["rounds"]),
            f"Game {game_index} needs at least one round.",
        )
        for round_index, round_entry in enumerate(game["rounds"], start=1):
            prefix = f"Game {game_index}, round {round_index}"
            _require(isinstance(round_entry, dict), f"{prefix} must be an object.")
            _require(
                isinstance(round_entry.get("gameplay_settings_snapshot"), dict),
                f"{prefix} lacks gameplay_settings_snapshot.",
            )
            _require(
                isinstance(round_entry.get("initial_state"), dict),
                f"{prefix} lacks initial_state.",
            )
            _require(isinstance(round_entry.get("final_state"), dict), f"{prefix} lacks final_state.")
            _require(
                isinstance(round_entry.get("plays"), list) and bool(round_entry["plays"]),
                f"{prefix} needs at least one play.",
            )
            for prompt_index, prompt in enumerate(round_entry.get("prompts", []), start=1):
                _require(isinstance(prompt, dict), f"{prefix}, prompt {prompt_index} must be an object.")
                _require(
                    isinstance(prompt.get("bot_id"), int) and prompt["bot_id"] > 0,
                    f"{prefix}, prompt {prompt_index}: bot_id is invalid.",
                )
                _validate_protected_text(prompt.get("prompt"), f"{prefix}, prompt {prompt_index}.prompt")
                _require_content_mode(prompt["prompt"], privacy, f"{prefix}, prompt {prompt_index}.prompt")
            for play_index, play in enumerate(round_entry["plays"], start=1):
                play_prefix = f"{prefix}, play {play_index}"
                _require(isinstance(play, dict), f"{play_prefix} must be an object.")
                required = {
                    "play_id": str,
                    "sequence": int,
                    "bot_id": int,
                    "human_prompt": dict,
                    "system_instructions": dict,
                    "context_policy": dict,
                    "game_state_supplied_to_model": dict,
                    "request": dict,
                    "request_started_at": str,
                    "request_completed_at": str,
                    "latency_ms": (int, float),
                    "attempts": int,
                    "response": dict,
                    "normalized_command": str,
                    "pre_state": dict,
                    "post_state": dict,
                    "events": list,
                    "transition_sha256": str,
                    "play_sha256": str,
                    "chain_sha256": str,
                    "status": str,
                }
                for key, expected_type in required.items():
                    _require(
                        isinstance(play.get(key), expected_type),
                        f"{play_prefix}: {key} has an invalid type.",
                    )
                _require(play["sequence"] > 0, f"{play_prefix}: sequence must be positive.")
                _require(play["bot_id"] > 0, f"{play_prefix}: bot_id must be positive.")
                _require(play["attempts"] > 0, f"{play_prefix}: attempts must be positive.")
                _require(play["latency_ms"] >= 0, f"{play_prefix}: latency_ms cannot be negative.")
                _require(
                    play["status"] in {"ok", "invalid-command", "invocation-error"},
                    f"{play_prefix}: status is invalid.",
                )
                _validate_protected_text(play["human_prompt"], f"{play_prefix}.human_prompt")
                _validate_protected_text(play["system_instructions"], f"{play_prefix}.system_instructions")
                _validate_protected_text(play["response"], f"{play_prefix}.response")
                _require_content_mode(play["human_prompt"], privacy, f"{play_prefix}.human_prompt")
                _require_content_mode(play["system_instructions"], privacy, f"{play_prefix}.system_instructions")
                _require_content_mode(play["response"], privacy, f"{play_prefix}.response")
                context_policy = play["context_policy"]
                _require(
                    set(context_policy) == {"prompt_augmentation", "independent_contexts"}
                    and all(isinstance(value, bool) for value in context_policy.values()),
                    f"{play_prefix}: context_policy is invalid.",
                )
                request = play["request"]
                _require(
                    request.get("privacy_mode") in {mode.value for mode in PrivacyMode},
                    f"{play_prefix}: request privacy_mode is invalid.",
                )
                _require(
                    request.get("privacy_mode") == privacy.value,
                    f"{play_prefix}: request privacy mode does not match the session.",
                )
                if privacy is PrivacyMode.HASHED:
                    _require(
                        "payload" not in request and "stored_sha256" not in request,
                        f"{play_prefix}: hash-only request must not retain a payload.",
                    )
                else:
                    _require(
                        isinstance(request.get("payload"), dict),
                        f"{play_prefix}: retained request payload is required.",
                    )
                    _require("stored_sha256" in request, f"{play_prefix}: retained request hash is required.")
                _require_sha(
                    request.get("canonical_sha256"),
                    f"{play_prefix}.request.canonical_sha256",
                )
                if "stored_sha256" in request:
                    _require_sha(
                        request["stored_sha256"],
                        f"{play_prefix}.request.stored_sha256",
                    )
                _require_sha(
                    play["transition_sha256"],
                    f"{play_prefix}.transition_sha256",
                )
                _require_sha(play["play_sha256"], f"{play_prefix}.play_sha256")
                _require_sha(play["chain_sha256"], f"{play_prefix}.chain_sha256")
                _require_sha(
                    play.get("previous_play_sha256"),
                    f"{play_prefix}.previous_play_sha256",
                    nullable=True,
                )
                if play["status"] == "invocation-error":
                    _require(
                        play["normalized_command"] == "ERR",
                        f"{play_prefix}: invocation errors must ground to ERR.",
                    )
                    _require(
                        play["response"].get("length") == 0,
                        f"{play_prefix}: invocation errors must not claim a model response.",
                    )
                    _require(isinstance(play.get("error"), dict), f"{play_prefix}: error is required.")
                    _require(
                        isinstance(play["error"].get("type"), str)
                        and bool(play["error"]["type"]),
                        f"{play_prefix}: error.type is required.",
                    )
                    _validate_protected_text(play["error"].get("message"), f"{play_prefix}.error.message")
                    _require_content_mode(play["error"]["message"], privacy, f"{play_prefix}.error.message")
                else:
                    _require("error" not in play, f"{play_prefix}: error is only valid for invocation-error status.")
                    if play["status"] == "ok":
                        _require(play["normalized_command"] != "ERR", f"{play_prefix}: ok status cannot store ERR.")
                    if play["status"] == "invalid-command":
                        _require(play["normalized_command"] == "ERR", f"{play_prefix}: invalid-command must store ERR.")

                play_id = play["play_id"]
                _require(play_id not in seen_play_ids, f"Duplicate play_id: {play_id}")
                seen_play_ids.add(play_id)
                sequence = play["sequence"]
                _require(sequence not in seen_sequences, f"Duplicate sequence: {sequence}")
                seen_sequences.add(sequence)
    return payload


def verify_session_envelope_hash(payload: Mapping[str, Any]) -> bool:
    material = deepcopy(dict(payload))
    recorded = material.pop("session_sha256", None)
    return isinstance(recorded, str) and recorded == sha256_json(material)


def write_session_v3(payload: Mapping[str, Any], path: str | Path) -> Path:
    validated = validate_session_v3(dict(payload))
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(validated, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output


def load_session_v3(path: str | Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SessionV3Error(str(exc)) from exc
    return validate_session_v3(payload)
