"""Saved-session schema helpers for BatLLM and the analyzer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SESSION_SCHEMA_VERSION = 2
SESSION_TYPE = "batllm_saved_session"


class SessionFormatError(ValueError):
    """Raised when a session file cannot be understood."""


class UnsupportedLegacySession(SessionFormatError):
    """Raised when a legacy session is loaded into the analyzer."""


def build_session_payload(
    *,
    games: list[dict[str, Any]],
    app_version: str,
    saved_at: str,
) -> dict[str, Any]:
    """Build the current saved-session envelope."""
    return {
        "schema_version": SESSION_SCHEMA_VERSION,
        "session_type": SESSION_TYPE,
        "app_version": app_version,
        "saved_at": saved_at,
        "games": games,
    }


def _ensure(condition: bool, message: str) -> None:
    if not condition:
        raise SessionFormatError(message)


def validate_session_payload(payload: Any) -> dict[str, Any]:
    """Validate and return a v2 BatLLM saved-session payload."""
    if isinstance(payload, list):
        raise UnsupportedLegacySession(
            "This saved session uses the legacy BatLLM format. Save a new session to use Game Analyzer."
        )

    _ensure(isinstance(payload, dict), "Saved session must be a JSON object.")
    _ensure(payload.get("schema_version") == SESSION_SCHEMA_VERSION, "Unsupported schema_version.")
    _ensure(payload.get("session_type") == SESSION_TYPE, "Unsupported session_type.")

    games = payload.get("games")
    _ensure(isinstance(games, list), "Saved session must contain a games list.")

    for game_index, game in enumerate(games, start=1):
        _ensure(isinstance(game, dict), f"Game {game_index} must be an object.")
        rounds = game.get("rounds")
        _ensure(isinstance(rounds, list), f"Game {game_index} must contain rounds.")
        for round_index, round_entry in enumerate(rounds, start=1):
            _ensure(isinstance(round_entry, dict), f"Game {game_index} round {round_index} must be an object.")
            _ensure(
                isinstance(round_entry.get("gameplay_settings_snapshot"), dict),
                f"Game {game_index} round {round_index} is missing gameplay_settings_snapshot.",
            )
            _ensure(
                isinstance(round_entry.get("initial_state"), dict),
                f"Game {game_index} round {round_index} is missing initial_state.",
            )
            turns = round_entry.get("turns")
            _ensure(isinstance(turns, list), f"Game {game_index} round {round_index} must contain turns.")
            for turn_index, turn in enumerate(turns, start=1):
                _ensure(isinstance(turn, dict), f"Turn {turn_index} must be an object.")
                _ensure(isinstance(turn.get("pre_state"), dict), f"Turn {turn_index} missing pre_state.")
                _ensure(isinstance(turn.get("post_state"), dict), f"Turn {turn_index} missing post_state.")
                _ensure(isinstance(turn.get("plays"), list), f"Turn {turn_index} missing plays.")

    return payload


def load_session_payload(path: str | Path) -> dict[str, Any]:
    """Read and validate a saved-session payload."""
    path = Path(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SessionFormatError(f"Invalid JSON: {exc.msg}") from exc
    except OSError as exc:
        raise SessionFormatError(str(exc)) from exc

    return validate_session_payload(payload)


def summarize_session_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a small preview summary for analyzer UIs."""
    games = payload.get("games", [])
    round_count = sum(len((game or {}).get("rounds", [])) for game in games)
    turn_count = sum(
        len((round_entry or {}).get("turns", []))
        for game in games
        for round_entry in (game or {}).get("rounds", [])
    )
    return {
        "schema_version": payload.get("schema_version"),
        "session_type": payload.get("session_type"),
        "app_version": payload.get("app_version"),
        "saved_at": payload.get("saved_at"),
        "game_count": len(games),
        "round_count": round_count,
        "turn_count": turn_count,
    }
