"""Headless verifier for BatLLM research-session traces."""
# pylint: disable=too-many-arguments,too-many-branches,too-many-statements,too-many-locals

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import json
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping

from game.replay_engine import (
    GameplaySettingsSnapshot,
    apply_play,
    compare_state_maps,
    parse_model_response,
)
from game.session_v3 import (
    SessionV3Error,
    load_session_v3,
    validate_session_v3,
    verify_session_envelope_hash,
)
from game.trace_contract import (
    PrivacyMode,
    canonical_json,
    event_to_dict,
    transition_hash,
    verify_play_hashes,
    verify_protected_text,
    verify_request_record,
)


@dataclass
class VerificationIssue:
    level: str
    location: str
    code: str
    detail: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "level": self.level,
            "location": self.location,
            "code": self.code,
            "detail": self.detail,
        }


@dataclass
class VerificationReport:
    valid: bool = True
    schema_valid: bool = True
    envelope_integrity: bool = True
    request_records: int = 0
    exact_requests: int = 0
    redacted_requests: int = 0
    commitment_only_requests: int = 0
    grounding_records: int = 0
    verified_groundings: int = 0
    commitment_only_groundings: int = 0
    invocation_errors: int = 0
    transitions: int = 0
    replayed_transitions: int = 0
    state_equivalent_transitions: int = 0
    event_equivalent_transitions: int = 0
    integrity_valid_transitions: int = 0
    round_final_states_verified: int = 0
    game_final_states_verified: int = 0
    elapsed_ms: float = 0.0
    issues: list[VerificationIssue] = field(default_factory=list)

    def add_issue(
        self, level: str, location: str, code: str, detail: str = ""
    ) -> None:
        self.valid = False
        self.issues.append(VerificationIssue(level, location, code, detail))

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "schema_valid": self.schema_valid,
            "envelope_integrity": self.envelope_integrity,
            "request_records": self.request_records,
            "exact_requests": self.exact_requests,
            "redacted_requests": self.redacted_requests,
            "commitment_only_requests": self.commitment_only_requests,
            "grounding_records": self.grounding_records,
            "verified_groundings": self.verified_groundings,
            "commitment_only_groundings": self.commitment_only_groundings,
            "invocation_errors": self.invocation_errors,
            "transitions": self.transitions,
            "replayed_transitions": self.replayed_transitions,
            "state_equivalent_transitions": self.state_equivalent_transitions,
            "event_equivalent_transitions": self.event_equivalent_transitions,
            "integrity_valid_transitions": self.integrity_valid_transitions,
            "round_final_states_verified": self.round_final_states_verified,
            "game_final_states_verified": self.game_final_states_verified,
            "elapsed_ms": self.elapsed_ms,
            "issues": [issue.to_dict() for issue in self.issues],
        }


def _retained_text(
    record: Mapping[str, Any], privacy: PrivacyMode
) -> str | None:
    if privacy is not PrivacyMode.FULL:
        return None
    text = record.get("text")
    return str(text) if isinstance(text, str) else None


def _verify_grounding(
    play: Mapping[str, Any],
    report: VerificationReport,
    location: str,
    privacy: PrivacyMode,
) -> None:
    status = play.get("status")
    command = play.get("normalized_command")
    if status == "invocation-error":
        report.invocation_errors += 1
        if command != "ERR":
            report.add_issue(
                "R3", location, "invocation-error-command-mismatch"
            )
        return

    report.grounding_records += 1
    retained_response = _retained_text(play["response"], privacy)
    if retained_response is None:
        report.commitment_only_groundings += 1
        return
    parsed = parse_model_response(retained_response)
    if parsed.normalized_cmd == command:
        report.verified_groundings += 1
    else:
        report.add_issue(
            "R3",
            location,
            "grounding-mismatch",
            (
                f"response parses as {parsed.normalized_cmd!r}; "
                f"trace stores {command!r}"
            ),
        )
    expected_status = "invalid-command" if not parsed.valid else "ok"
    if status != expected_status:
        report.add_issue(
            "R3",
            location,
            "grounding-status-mismatch",
            f"response implies {expected_status!r}; trace stores {status!r}",
        )


def _request_user_content(
    *, prompt: str, game_state: Mapping[str, Any], augmented: bool
) -> str:
    if not augmented:
        return prompt
    return (
        "[GAME_STATE]\n"
        + json.dumps(
            game_state,
            separators=(",", ":"),
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n[PLAYER_INPUT]\n"
        + prompt
    )


def _ensure_system_message(
    history: list[dict[str, str]], system_instructions: str
) -> None:
    if not system_instructions:
        return
    system_message = {"role": "system", "content": system_instructions}
    if not history or history[0].get("role") != "system":
        history.insert(0, system_message)
    elif history[0] != system_message:
        history[0] = system_message


def _verify_request_semantics(
    *,
    play: Mapping[str, Any],
    session_model: Mapping[str, Any],
    histories_by_bot: dict[int, list[dict[str, str]]],
    shared_history: list[dict[str, str]],
    report: VerificationReport,
    location: str,
    privacy: PrivacyMode,
) -> None:
    """Verify cross-field request consistency and full-mode reconstruction."""

    request = play["request"]
    expected_game_state = {"bots": deepcopy(play["pre_state"])}
    if canonical_json(play["game_state_supplied_to_model"]) != canonical_json(
        expected_game_state
    ):
        report.add_issue(
            "R2", location, "request-game-state-mismatch"
        )

    payload = request.get("payload")
    if not isinstance(payload, Mapping):
        return

    messages = payload.get("messages")
    if not isinstance(messages, list) or not all(
        isinstance(message, Mapping)
        and isinstance(message.get("role"), str)
        and "content" in message
        for message in messages
    ):
        report.add_issue("R2", location, "request-messages-invalid")
    if payload.get("stream") is not False:
        report.add_issue("R2", location, "request-stream-setting-mismatch")
    if not isinstance(payload.get("options"), Mapping):
        report.add_issue("R2", location, "request-options-invalid")

    for request_key, provenance_key in (
        ("provider", "provider"),
        ("endpoint", "endpoint"),
        ("model", "requested_model"),
    ):
        expected = session_model.get(provenance_key)
        if expected is not None and payload.get(request_key) != expected:
            report.add_issue(
                "R2",
                location,
                "request-provenance-mismatch",
                (
                    f"request {request_key}={payload.get(request_key)!r}; "
                    f"session {provenance_key}={expected!r}"
                ),
            )

    if privacy is not PrivacyMode.FULL:
        return

    prompt = _retained_text(play["human_prompt"], privacy)
    system = _retained_text(play["system_instructions"], privacy)
    if prompt is None or system is None:
        report.add_issue("R2", location, "full-request-source-text-missing")
        return

    context_policy = play["context_policy"]
    independent = bool(context_policy["independent_contexts"])
    history = (
        histories_by_bot.setdefault(int(play["bot_id"]), [])
        if independent
        else shared_history
    )
    _ensure_system_message(history, system)
    user_content = _request_user_content(
        prompt=prompt,
        game_state=play["game_state_supplied_to_model"],
        augmented=bool(context_policy["prompt_augmentation"]),
    )
    expected_messages = deepcopy(history)
    expected_messages.append({"role": "user", "content": user_content})
    if canonical_json(payload.get("messages")) != canonical_json(expected_messages):
        report.add_issue(
            "R2", location, "exact-request-reconstruction-mismatch"
        )

    if play.get("status") != "invocation-error":
        response = _retained_text(play["response"], privacy)
        if response is None:
            report.add_issue("R2", location, "full-response-text-missing")
            return
        history.append({"role": "user", "content": user_content})
        history.append({"role": "assistant", "content": response})


def _compare_recorded_state(
    *,
    derived: Mapping[Any, Mapping[str, Any]],
    recorded: Mapping[Any, Mapping[str, Any]],
    report: VerificationReport,
    level: str,
    location: str,
    code: str,
) -> bool:
    equivalent, details = compare_state_maps(derived, recorded)
    if not equivalent:
        report.add_issue(level, location, code, "; ".join(details))
    return equivalent


def verify_payload(payload: Mapping[str, Any]) -> VerificationReport:
    started = perf_counter()
    report = VerificationReport()
    try:
        validate_session_v3(dict(payload))
    except SessionV3Error as exc:
        report.schema_valid = False
        report.add_issue("R1", "session", "schema-invalid", str(exc))
        report.elapsed_ms = (perf_counter() - started) * 1000.0
        return report

    try:
        canonical_json(payload)
    except (TypeError, ValueError) as exc:
        report.add_issue("R1", "session", "non-canonical-value", str(exc))
        report.elapsed_ms = (perf_counter() - started) * 1000.0
        return report

    privacy = PrivacyMode(payload["privacy_mode"])

    if not verify_session_envelope_hash(payload):
        report.envelope_integrity = False
        report.add_issue("R1", "session", "session-hash-mismatch")

    expected_previous: str | None = None
    expected_sequence = 1
    session_model = payload.get("model_provenance", {})

    for game_index, game in enumerate(payload.get("games", []), start=1):
        histories_by_bot: dict[int, list[dict[str, str]]] = {}
        shared_history: list[dict[str, str]] = []
        last_game_state: Mapping[Any, Mapping[str, Any]] | None = None
        previous_round_final: Mapping[Any, Mapping[str, Any]] | None = None

        for round_index, round_entry in enumerate(game.get("rounds", []), start=1):
            round_location = f"game[{game_index}].round[{round_index}]"
            if previous_round_final is not None:
                _compare_recorded_state(
                    derived=previous_round_final,
                    recorded=round_entry.get("initial_state", {}),
                    report=report,
                    level="R1",
                    location=round_location,
                    code="round-initial-state-mismatch",
                )
            prior_post_state = deepcopy(round_entry.get("initial_state", {}))
            rules = GameplaySettingsSnapshot.from_mapping(
                round_entry.get("gameplay_settings_snapshot")
            )
            for play_index, play in enumerate(round_entry.get("plays", []), start=1):
                location = (
                    f"game[{game_index}].round[{round_index}].play[{play_index}]"
                )
                if play.get("sequence") != expected_sequence:
                    report.add_issue(
                        "R1",
                        location,
                        "sequence-mismatch",
                        (
                            f"expected {expected_sequence}; "
                            f"found {play.get('sequence')!r}"
                        ),
                    )
                expected_sequence += 1

                report.request_records += 1
                request_ok, request_level = verify_request_record(play["request"])
                if request_level == "exact-reconstruction":
                    report.exact_requests += 1
                elif request_level == "redacted-structure":
                    report.redacted_requests += 1
                elif request_level == "commitment-only":
                    report.commitment_only_requests += 1
                if not request_ok:
                    report.add_issue("R2", location, request_level)

                for key, code in (
                    ("human_prompt", "prompt-commitment-mismatch"),
                    ("system_instructions", "system-commitment-mismatch"),
                    ("response", "response-commitment-mismatch"),
                ):
                    if not verify_protected_text(play[key], privacy):
                        report.add_issue("R2", location, code)
                error_record = play.get("error")
                if isinstance(error_record, Mapping) and isinstance(
                    error_record.get("message"), Mapping
                ):
                    if not verify_protected_text(
                        error_record["message"], privacy
                    ):
                        report.add_issue(
                            "R2", location, "error-commitment-mismatch"
                        )

                _verify_request_semantics(
                    play=play,
                    session_model=session_model,
                    histories_by_bot=histories_by_bot,
                    shared_history=shared_history,
                    report=report,
                    location=location,
                    privacy=privacy,
                )
                _verify_grounding(play, report, location, privacy)

                hashes_ok, hash_errors = verify_play_hashes(
                    play, expected_previous
                )
                if not hashes_ok:
                    for error in hash_errors:
                        report.add_issue("R1", location, error)
                expected_previous = play.get("play_sha256")

                report.transitions += 1
                expected_transition_hash = transition_hash(
                    bot_id=play["bot_id"],
                    pre_state=play["pre_state"],
                    command=play["normalized_command"],
                    rules=round_entry["gameplay_settings_snapshot"],
                    post_state=play["post_state"],
                    events=play["events"],
                )
                if expected_transition_hash == play["transition_sha256"]:
                    report.integrity_valid_transitions += 1
                else:
                    report.add_issue(
                        "R1", location, "transition-hash-mismatch"
                    )

                _compare_recorded_state(
                    derived=play["pre_state"],
                    recorded=prior_post_state,
                    report=report,
                    level="R1",
                    location=location,
                    code="state-continuity-mismatch",
                )

                resolution = apply_play(
                    play["pre_state"],
                    bot_id=play["bot_id"],
                    llm_response=play["normalized_command"],
                    cmd_text=play["normalized_command"],
                    rules=rules,
                )
                report.replayed_transitions += 1
                if _compare_recorded_state(
                    derived=resolution.state_by_bot,
                    recorded=play["post_state"],
                    report=report,
                    level="R4",
                    location=location,
                    code="replay-state-mismatch",
                ):
                    report.state_equivalent_transitions += 1

                replay_events = [
                    event_to_dict(event) for event in resolution.events
                ]
                if canonical_json(replay_events) == canonical_json(play["events"]):
                    report.event_equivalent_transitions += 1
                else:
                    report.add_issue("R4", location, "replay-event-mismatch")
                prior_post_state = deepcopy(play["post_state"])

            if _compare_recorded_state(
                derived=prior_post_state,
                recorded=round_entry["final_state"],
                report=report,
                level="R1",
                location=round_location,
                code="round-final-state-mismatch",
            ):
                report.round_final_states_verified += 1
            last_game_state = round_entry["final_state"]
            previous_round_final = deepcopy(round_entry["final_state"])

        if last_game_state is not None:
            game_location = f"game[{game_index}]"
            if _compare_recorded_state(
                derived=last_game_state,
                recorded=game["final_state"],
                report=report,
                level="R1",
                location=game_location,
                code="game-final-state-mismatch",
            ):
                report.game_final_states_verified += 1

    report.elapsed_ms = (perf_counter() - started) * 1000.0
    report.valid = not report.issues
    return report


def verify_file(path: str | Path) -> VerificationReport:
    try:
        payload = load_session_v3(path)
    except SessionV3Error as exc:
        report = VerificationReport(valid=False, schema_valid=False)
        report.add_issue("R1", "session", "schema-invalid", str(exc))
        return report
    return verify_payload(payload)


def format_report(report: VerificationReport) -> str:
    status = "PASS" if report.valid else "FAIL"
    lines = [
        f"schema: {'valid' if report.schema_valid else 'invalid'}",
        (
            "envelope integrity: "
            f"{'valid' if report.envelope_integrity else 'invalid'}"
        ),
        (
            "request reconstruction: "
            f"exact={report.exact_requests} "
            f"redacted={report.redacted_requests} "
            f"commitment-only={report.commitment_only_requests}"
        ),
        (
            "response grounding: "
            f"verified={report.verified_groundings} "
            f"commitment-only={report.commitment_only_groundings} "
            f"invocation-errors={report.invocation_errors}"
        ),
        (
            "transition integrity: "
            f"{report.integrity_valid_transitions}/{report.transitions}"
        ),
        f"transition replay: {report.replayed_transitions}/{report.transitions}",
        (
            "state equivalence: "
            f"{report.state_equivalent_transitions}/{report.transitions}"
        ),
        (
            "event equivalence: "
            f"{report.event_equivalent_transitions}/{report.transitions}"
        ),
        f"elapsed: {report.elapsed_ms:.3f} ms",
        f"result: {status}",
    ]
    for issue in report.issues:
        suffix = f" — {issue.detail}" if issue.detail else ""
        lines.append(f"[{issue.level}] {issue.location}: {issue.code}{suffix}")
    return "\n".join(lines)


def write_json_report(report: VerificationReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=False, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return output
