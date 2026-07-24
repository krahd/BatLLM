from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from game.replay_engine import (
    GameplaySettingsSnapshot,
    parse_model_response,
    resolve_shot,
)
from game.research_runtime import (
    InvocationPolicy,
    MediatedGameRuntime,
    ScriptedClient,
    extract_response_text,
)
from game.session_v3 import (
    validate_session_v3,
    verify_session_envelope_hash,
    write_session_v3,
)
from game.trace_contract import (
    PrivacyMode,
    canonical_json,
    event_to_dict,
    sha256_json,
)
from game.trace_verifier import verify_payload


def initial_state() -> dict[int, dict[str, object]]:
    return {
        1: {
            "id": 1,
            "health": 30,
            "x": 0.2,
            "y": 0.5,
            "rot": 0,
            "shield": False,
        },
        2: {
            "id": 2,
            "health": 30,
            "x": 0.8,
            "y": 0.5,
            "rot": 180,
            "shield": False,
        },
    }


def rules() -> GameplaySettingsSnapshot:
    return GameplaySettingsSnapshot.from_mapping(
        {
            "bot_diameter": 0.1,
            "bot_step_length": 0.03,
            "bullet_damage": 5,
            "bullet_diameter": 0.02,
            "bullet_step_length": 0.01,
            "shield_size": 70,
            "shield_initial_state": False,
            "initial_health": 30,
            "turns_per_round": 4,
            "total_rounds": 1,
        }
    )


def build(mode: PrivacyMode = PrivacyMode.FULL) -> dict:
    runtime = MediatedGameRuntime(
        client=ScriptedClient(["M", "S1", "C90", "B"]),
        initial_state=initial_state(),
        rules=rules(),
        policy=InvocationPolicy(provider="scripted", model="fixture"),
        system_instructions="Return one command.",
        privacy_mode=mode,
    )
    runtime.start_round({1: "advance", 2: "defend"})
    runtime.run_turn({1: "advance", 2: "defend"})
    runtime.run_turn({1: "turn", 2: "fire"})
    return runtime.session_payload()


def test_canonical_hash_is_order_independent() -> None:
    assert canonical_json({"b": 2, "a": 1}) == canonical_json(
        {"a": 1, "b": 2}
    )
    assert sha256_json({"b": 2, "a": 1}) == sha256_json(
        {"a": 1, "b": 2}
    )



def test_semantic_events_do_not_leak_raw_model_text() -> None:
    event = {
        "type": "invalid_command",
        "label": "Invalid command",
        "details": {"raw_response": "private text", "cmd": "ERR"},
    }
    converted = event_to_dict(event)
    assert converted["details"] == {"cmd": "ERR"}
    assert "private text" not in canonical_json(converted)

def test_full_trace_is_exactly_reconstructable_and_replayable() -> None:
    payload = build()
    validate_session_v3(payload)
    assert verify_session_envelope_hash(payload)
    report = verify_payload(payload)
    assert report.valid
    assert report.exact_requests == 4
    assert report.verified_groundings == 4
    assert report.state_equivalent_transitions == 4
    assert report.event_equivalent_transitions == 4


def test_privacy_modes_preserve_operative_replay() -> None:
    redacted = verify_payload(build(PrivacyMode.REDACTED))
    hashed = verify_payload(build(PrivacyMode.HASHED))
    assert redacted.valid and redacted.redacted_requests == 4
    assert hashed.valid and hashed.commitment_only_requests == 4
    assert redacted.commitment_only_groundings == 4
    assert hashed.commitment_only_groundings == 4
    assert redacted.state_equivalent_transitions == 4
    assert hashed.state_equivalent_transitions == 4


def test_grounding_corruption_is_detected_even_with_recomputed_hashes() -> None:
    corrupted = deepcopy(build())
    play = corrupted["games"][0]["rounds"][0]["plays"][0]
    play["normalized_command"] = "C90"
    # Deliberately leave integrity commitments stale: the verifier should report
    # both semantic and integrity failures rather than silently accepting either.
    report = verify_payload(corrupted)
    assert not report.valid
    codes = {issue.code for issue in report.issues}
    assert "grounding-mismatch" in codes
    assert "play-hash-mismatch" in codes


def test_invocation_failure_is_recorded_as_replayable_err() -> None:
    class FailingClient:
        def chat(self, **_kwargs):
            raise TimeoutError("fixture timeout")

    runtime = MediatedGameRuntime(
        client=FailingClient(),
        initial_state=initial_state(),
        rules=rules(),
        policy=InvocationPolicy(
            provider="fixture", model="failure", max_attempts=2
        ),
        privacy_mode=PrivacyMode.FULL,
    )
    runtime.start_round({1: "act"})
    play = runtime.play(bot_id=1, human_prompt="act")
    assert play["status"] == "invocation-error"
    assert play["attempts"] == 2
    assert play["normalized_command"] == "ERR"
    assert play["error"]["type"] == "TimeoutError"
    report = verify_payload(runtime.session_payload())
    assert report.valid
    assert report.verified_groundings == 0
    assert report.invocation_errors == 1


def test_round_trip_file(tmp_path: Path) -> None:
    path = write_session_v3(build(), tmp_path / "trace.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert verify_payload(data).valid


def test_verifier_reports_invalid_gameplay_settings() -> None:
    corrupted = deepcopy(build())
    corrupted["games"][0]["rounds"][0]["gameplay_settings_snapshot"][
        "bot_step_length"
    ] = 0

    report = verify_payload(corrupted)

    assert not report.valid
    assert "invalid-gameplay-settings" in {issue.code for issue in report.issues}


def test_verifier_reports_infinite_integer_gameplay_setting() -> None:
    corrupted = deepcopy(build())
    corrupted["games"][0]["rounds"][0]["gameplay_settings_snapshot"][
        "turns_per_round"
    ] = float("inf")

    report = verify_payload(corrupted)

    assert not report.valid
    assert "invalid-gameplay-settings" in {issue.code for issue in report.issues}


def test_v3_validation_rejects_non_mapping_nested_bot_state() -> None:
    corrupted = deepcopy(build())
    corrupted["games"][0]["rounds"][0]["plays"][0]["pre_state"][1] = "invalid"

    report = verify_payload(corrupted)

    assert not report.valid
    assert not report.schema_valid


def test_full_request_history_is_independently_reconstructed() -> None:
    corrupted = deepcopy(build())
    play = corrupted["games"][0]["rounds"][0]["plays"][1]
    play["request"]["payload"]["messages"][-1]["content"] = "different"
    report = verify_payload(corrupted)
    assert not report.valid
    assert "exact-request-reconstruction-mismatch" in {
        issue.code for issue in report.issues
    }


def test_request_model_must_match_session_provenance() -> None:
    corrupted = deepcopy(build())
    play = corrupted["games"][0]["rounds"][0]["plays"][0]
    play["request"]["payload"]["model"] = "different"
    report = verify_payload(corrupted)
    assert not report.valid
    assert "request-provenance-mismatch" in {
        issue.code for issue in report.issues
    }


def test_game_state_supplied_to_model_must_match_pre_state() -> None:
    corrupted = deepcopy(build())
    play = corrupted["games"][0]["rounds"][0]["plays"][0]
    play["game_state_supplied_to_model"]["bots"][1]["x"] = 0.99
    report = verify_payload(corrupted)
    assert not report.valid
    assert "request-game-state-mismatch" in {
        issue.code for issue in report.issues
    }

def test_exact_response_text_is_preserved() -> None:
    assert extract_response_text("  M  ") == "  M  "


def test_command_grammar_rejects_suffixes_and_non_finite_numbers() -> None:
    for response in ("BLAH", "S10", "S01", "Mnan", "Minf", "Cnan", "Ainf"):
        parsed = parse_model_response(response)
        assert not parsed.valid
        assert parsed.normalized_cmd == "ERR"


def test_zero_bullet_step_is_rejected() -> None:
    with pytest.raises(ValueError, match="step lengths must be positive"):
        GameplaySettingsSnapshot.from_mapping(
            {**rules().to_dict(), "bullet_step_length": 0.0}
        )


def test_full_mode_accepts_literal_redaction_marker() -> None:
    runtime = MediatedGameRuntime(
        client=ScriptedClient(["[REDACTED]"]),
        initial_state=initial_state(),
        rules=rules(),
        policy=InvocationPolicy(provider="scripted", model="fixture"),
        privacy_mode=PrivacyMode.FULL,
    )
    runtime.start_round({1: "[REDACTED]"})
    play = runtime.play(bot_id=1, human_prompt="[REDACTED]")
    assert play["response"]["text"] == "[REDACTED]"
    report = verify_payload(runtime.session_payload())
    assert report.valid
    assert report.verified_groundings == 1


def test_canonicalisation_rejects_stringified_key_collisions() -> None:
    with pytest.raises(ValueError, match="collide"):
        canonical_json({1: "integer", "1": "string"})


def test_round_initial_state_must_follow_previous_round() -> None:
    runtime = MediatedGameRuntime(
        client=ScriptedClient(["M", "M"]),
        initial_state=initial_state(),
        rules=rules(),
        policy=InvocationPolicy(provider="scripted", model="fixture"),
        privacy_mode=PrivacyMode.FULL,
    )
    runtime.start_round({1: "advance"})
    runtime.play(bot_id=1, human_prompt="advance")
    runtime.end_round()
    runtime.start_round({1: "advance again"})
    runtime.play(bot_id=1, human_prompt="advance again")
    payload = runtime.session_payload()
    payload["games"][0]["rounds"][1]["initial_state"][1]["x"] = 0.99
    report = verify_payload(payload)
    assert not report.valid
    assert "round-initial-state-mismatch" in {
        issue.code for issue in report.issues
    }


def test_event_fallback_does_not_stringify_private_objects() -> None:
    class PrivateEvent:
        def __str__(self) -> str:
            return "private model response"

    converted = event_to_dict(PrivateEvent())
    assert "private model response" not in canonical_json(converted)
