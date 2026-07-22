#!/usr/bin/env python3
"""Apply the final adversarial fixes to the URUCON branch sources."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one occurrence, found {count}: {old[:80]!r}")
    write(path, text.replace(old, new, 1))


def replace_between(path: str, start: str, end: str, replacement: str) -> None:
    text = read(path)
    start_index = text.find(start)
    if start_index < 0:
        raise RuntimeError(f"{path}: start marker not found: {start!r}")
    end_index = text.find(end, start_index)
    if end_index < 0:
        raise RuntimeError(f"{path}: end marker not found: {end!r}")
    write(path, text[:start_index] + replacement.rstrip() + "\n\n\n" + text[end_index:])


def append_once(path: str, marker: str, addition: str) -> None:
    text = read(path)
    if marker in text:
        return
    write(path, text.rstrip() + "\n\n" + addition.rstrip() + "\n")


replace_once(
    "src/game/research_runtime.py",
    '''    text = str(text or "").strip()\n    if not text:\n        raise RuntimeError(f"Empty model response ({type(response).__name__}).")\n    return text\n''',
    '''    text = str(text or "")\n    if not text.strip():\n        raise RuntimeError(f"Empty model response ({type(response).__name__}).")\n    return text\n''',
)

production_parser = '''def _parse_finite_number(fragment: str) -> float | None:
    """Parse a finite command argument without accepting surrounding whitespace."""

    if not fragment or fragment != fragment.strip():
        return None
    try:
        value = float(fragment)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def parse_model_response(response: Any) -> ParsedCommand:
    """Parse BatLLM's bounded command grammar into a normalised command."""

    raw = str(response or "").strip()
    if not raw:
        return ParsedCommand(
            raw_response=raw,
            normalized_cmd="ERR",
            kind="invalid",
            valid=False,
        )

    head = raw[0].upper()
    if head == "M":
        if len(raw) == 1:
            return ParsedCommand(raw_response=raw, normalized_cmd="M", kind="move")
        distance = _parse_finite_number(raw[1:])
        if distance is None:
            return ParsedCommand(
                raw_response=raw,
                normalized_cmd="ERR",
                kind="invalid",
                valid=False,
            )
        return ParsedCommand(
            raw_response=raw,
            normalized_cmd=f"M{distance}",
            kind="move",
            value=distance,
        )

    if head in {"C", "A"}:
        angle = _parse_finite_number(raw[1:])
        if angle is None:
            return ParsedCommand(
                raw_response=raw,
                normalized_cmd="ERR",
                kind="invalid",
                valid=False,
            )
        kind = "rotate_cw" if head == "C" else "rotate_ccw"
        return ParsedCommand(
            raw_response=raw,
            normalized_cmd=f"{head}{angle}",
            kind=kind,
            value=angle,
        )

    if head == "B" and len(raw) == 1:
        return ParsedCommand(raw_response=raw, normalized_cmd="B", kind="shoot")

    if head == "S":
        if len(raw) == 1:
            return ParsedCommand(
                raw_response=raw,
                normalized_cmd="S",
                kind="shield_toggle",
            )
        if len(raw) == 2 and raw[1] in {"0", "1"}:
            return ParsedCommand(
                raw_response=raw,
                normalized_cmd=f"S{raw[1]}",
                kind="shield_set",
                value=float(raw[1]),
            )

    return ParsedCommand(
        raw_response=raw,
        normalized_cmd="ERR",
        kind="invalid",
        valid=False,
    )'''
replace_between(
    "src/game/replay_engine.py",
    "def parse_model_response(response: Any) -> ParsedCommand:",
    "def compute_move_target(",
    production_parser,
)
replace_once(
    "src/game/replay_engine.py",
    '''    a = dx**2 + dy**2\n    b = 2 * (fx * dx + fy * dy)\n''',
    '''    a = dx**2 + dy**2\n    if math.isclose(a, 0.0, abs_tol=1e-15):\n        return False, False\n    b = 2 * (fx * dx + fy * dy)\n''',
)

reference_parser = '''def _parse_finite_number(fragment: str) -> float | None:
    if not fragment or fragment != fragment.strip():
        return None
    try:
        value = float(fragment)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def parse_command(response: Any) -> ReferenceCommand:
    """Implement the exact bounded command forms used by BatLLM."""

    raw = str(response or "").strip()
    if not raw:
        return ReferenceCommand("ERR", "invalid", valid=False)
    head = raw[0].upper()
    if head == "M":
        if len(raw) == 1:
            return ReferenceCommand("M", "move")
        distance = _parse_finite_number(raw[1:])
        if distance is None:
            return ReferenceCommand("ERR", "invalid", valid=False)
        return ReferenceCommand(f"M{distance}", "move", distance)
    if head in {"C", "A"}:
        angle = _parse_finite_number(raw[1:])
        if angle is None:
            return ReferenceCommand("ERR", "invalid", valid=False)
        kind = "rotate_cw" if head == "C" else "rotate_ccw"
        return ReferenceCommand(f"{head}{angle}", kind, angle)
    if head == "B" and len(raw) == 1:
        return ReferenceCommand("B", "shoot")
    if head == "S":
        if len(raw) == 1:
            return ReferenceCommand("S", "shield_toggle")
        if len(raw) == 2 and raw[1] in {"0", "1"}:
            return ReferenceCommand(
                f"S{raw[1]}", "shield_set", float(raw[1])
            )
    return ReferenceCommand("ERR", "invalid", valid=False)'''
replace_between(
    "research/urucon2026/experiments/reference_semantics.py",
    "def parse_command(response: Any) -> ReferenceCommand:",
    "def _event(",
    reference_parser,
)
replace_once(
    "research/urucon2026/experiments/differential_semantics.py",
    '''        "Sx",\n        "",\n''',
    '''        "Sx",\n        "S10",\n        "S01",\n        "BLAH",\n        "Mnan",\n        "Minf",\n        "Cnan",\n        "Ainf",\n        "",\n''',
)

replace_once(
    "src/game/trace_contract.py",
    '''    if isinstance(value, Mapping):\n        return {str(key): _normalise(item) for key, item in value.items()}\n''',
    '''    if isinstance(value, Mapping):\n        normalised: dict[str, Any] = {}\n        for key, item in value.items():\n            rendered_key = str(key)\n            if rendered_key in normalised:\n                raise ValueError(\n                    "Canonical mapping keys collide after string conversion: "\n                    f"{rendered_key!r}."\n                )\n            normalised[rendered_key] = _normalise(item)\n        return normalised\n''',
)
verify_protected = '''def verify_protected_text(
    value: Mapping[str, Any], expected_mode: PrivacyMode | str | None = None
) -> bool:
    """Verify retention form and retained full text when it is available."""

    try:
        privacy = (
            PrivacyMode(expected_mode)
            if expected_mode is not None
            else protected_text_mode(value)
        )
    except (TypeError, ValueError):
        return False
    if privacy is PrivacyMode.HASHED:
        return "text" not in value
    if privacy is PrivacyMode.REDACTED:
        return value.get("text") == REDACTED_TEXT
    if "text" not in value or not isinstance(value.get("text"), str):
        return False
    rendered = value["text"]
    return (
        value.get("sha256") == sha256_text(rendered)
        and value.get("length") == len(rendered)
        and value.get("encoding") == "utf-8"
    )'''
replace_between(
    "src/game/trace_contract.py",
    "def verify_protected_text(value: Mapping[str, Any]) -> bool:",
    "def _redact_message(",
    verify_protected,
)
replace_once(
    "src/game/trace_contract.py",
    '''        if content.get("redacted") is not True:\n            return False\n        digest = content.get("canonical_sha256")\n        if not isinstance(digest, str) or len(digest) != 64:\n            return False\n''',
    '''        role = message.get("role")\n        if not isinstance(role, str) or not role:\n            return False\n        if content.get("redacted") is not True:\n            return False\n        digest = content.get("canonical_sha256")\n        if (\n            not isinstance(digest, str)\n            or len(digest) != 64\n            or any(character not in "0123456789abcdef" for character in digest)\n        ):\n            return False\n        if not isinstance(content.get("original_type"), str):\n            return False\n''',
)
replace_once(
    "src/game/trace_contract.py",
    '''    else:\n        return {"type": type(event).__name__, "label": str(event)}\n''',
    '''    else:\n        event_type = type(event).__name__\n        return {"type": event_type, "label": event_type}\n''',
)

retention_validation = '''def _require_content_mode(
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
        )'''
replace_between(
    "src/game/session_v3.py",
    "def _require_content_mode(",
    "def validate_session_v3(",
    retention_validation,
)
replace_once(
    "src/game/session_v3.py",
    '''    protected_text_mode,\n''',
    "",
)

retained_text = '''def _retained_text(
    record: Mapping[str, Any], privacy: PrivacyMode
) -> str | None:
    if privacy is not PrivacyMode.FULL:
        return None
    text = record.get("text")
    return str(text) if isinstance(text, str) else None'''
replace_between(
    "src/game/trace_verifier.py",
    "def _retained_text(record: Mapping[str, Any]) -> str | None:",
    "def _verify_grounding(",
    retained_text,
)
replace_once(
    "src/game/trace_verifier.py",
    '''def _verify_grounding(\n    play: Mapping[str, Any], report: VerificationReport, location: str\n) -> None:\n''',
    '''def _verify_grounding(\n    play: Mapping[str, Any],\n    report: VerificationReport,\n    location: str,\n    privacy: PrivacyMode,\n) -> None:\n''',
)
replace_once(
    "src/game/trace_verifier.py",
    '''    retained_response = _retained_text(play["response"])\n''',
    '''    retained_response = _retained_text(play["response"], privacy)\n''',
)
replace_once(
    "src/game/trace_verifier.py",
    '''    report: VerificationReport,\n    location: str,\n) -> None:\n    """Verify cross-field request consistency and full-mode reconstruction."""\n''',
    '''    report: VerificationReport,\n    location: str,\n    privacy: PrivacyMode,\n) -> None:\n    """Verify cross-field request consistency and full-mode reconstruction."""\n''',
)
replace_once(
    "src/game/trace_verifier.py",
    '''    payload = request.get("payload")\n    if not isinstance(payload, Mapping):\n        return\n\n    for request_key, provenance_key in (\n''',
    '''    payload = request.get("payload")\n    if not isinstance(payload, Mapping):\n        return\n\n    messages = payload.get("messages")\n    if not isinstance(messages, list) or not all(\n        isinstance(message, Mapping)\n        and isinstance(message.get("role"), str)\n        and "content" in message\n        for message in messages\n    ):\n        report.add_issue("R2", location, "request-messages-invalid")\n    if payload.get("stream") is not False:\n        report.add_issue("R2", location, "request-stream-setting-mismatch")\n    if not isinstance(payload.get("options"), Mapping):\n        report.add_issue("R2", location, "request-options-invalid")\n\n    for request_key, provenance_key in (\n''',
)
replace_once(
    "src/game/trace_verifier.py",
    '''    if request.get("privacy_mode") != PrivacyMode.FULL.value:\n        return\n\n    prompt = _retained_text(play["human_prompt"])\n    system = _retained_text(play["system_instructions"])\n''',
    '''    if privacy is not PrivacyMode.FULL:\n        return\n\n    prompt = _retained_text(play["human_prompt"], privacy)\n    system = _retained_text(play["system_instructions"], privacy)\n''',
)
replace_once(
    "src/game/trace_verifier.py",
    '''        response = _retained_text(play["response"])\n''',
    '''        response = _retained_text(play["response"], privacy)\n''',
)
replace_once(
    "src/game/trace_verifier.py",
    '''    if payload.get("stream") is not False:\n        report.add_issue("R2", location, "request-stream-setting-mismatch")\n    if not isinstance(payload.get("options"), Mapping):\n        report.add_issue("R2", location, "request-options-invalid")\n\n    if play.get("status") != "invocation-error":\n''',
    '''    if play.get("status") != "invocation-error":\n''',
)
replace_once(
    "src/game/trace_verifier.py",
    '''    if not verify_session_envelope_hash(payload):\n''',
    '''    try:\n        canonical_json(payload)\n    except (TypeError, ValueError) as exc:\n        report.add_issue("R1", "session", "non-canonical-value", str(exc))\n        report.elapsed_ms = (perf_counter() - started) * 1000.0\n        return report\n\n    privacy = PrivacyMode(payload["privacy_mode"])\n\n    if not verify_session_envelope_hash(payload):\n''',
)
replace_once(
    "src/game/trace_verifier.py",
    '''        last_game_state: Mapping[Any, Mapping[str, Any]] | None = None\n\n        for round_index, round_entry in enumerate(game.get("rounds", []), start=1):\n            prior_post_state = deepcopy(round_entry.get("initial_state", {}))\n''',
    '''        last_game_state: Mapping[Any, Mapping[str, Any]] | None = None\n        previous_round_final: Mapping[Any, Mapping[str, Any]] | None = None\n\n        for round_index, round_entry in enumerate(game.get("rounds", []), start=1):\n            round_location = f"game[{game_index}].round[{round_index}]"\n            if previous_round_final is not None:\n                _compare_recorded_state(\n                    derived=previous_round_final,\n                    recorded=round_entry.get("initial_state", {}),\n                    report=report,\n                    level="R1",\n                    location=round_location,\n                    code="round-initial-state-mismatch",\n                )\n            prior_post_state = deepcopy(round_entry.get("initial_state", {}))\n''',
)
replace_once(
    "src/game/trace_verifier.py",
    '''            round_location = f"game[{game_index}].round[{round_index}]"\n            if _compare_recorded_state(\n''',
    '''            if _compare_recorded_state(\n''',
)
replace_once(
    "src/game/trace_verifier.py",
    '''            last_game_state = round_entry["final_state"]\n''',
    '''            last_game_state = round_entry["final_state"]\n            previous_round_final = deepcopy(round_entry["final_state"])\n''',
)
replace_once(
    "src/game/trace_verifier.py",
    '''                    if not verify_protected_text(play[key]):\n''',
    '''                    if not verify_protected_text(play[key], privacy):\n''',
)
replace_once(
    "src/game/trace_verifier.py",
    '''                    if not verify_protected_text(error_record["message"]):\n''',
    '''                    if not verify_protected_text(\n                        error_record["message"], privacy\n                    ):\n''',
)
replace_once(
    "src/game/trace_verifier.py",
    '''                    report=report,\n                    location=location,\n                )\n                _verify_grounding(play, report, location)\n''',
    '''                    report=report,\n                    location=location,\n                    privacy=privacy,\n                )\n                _verify_grounding(play, report, location, privacy)\n''',
)

replace_once(
    "src/tests/test_trace_contract.py",
    "import json\nfrom pathlib import Path\n",
    "import json\nfrom pathlib import Path\n\nimport pytest\n",
)
replace_once(
    "src/tests/test_trace_contract.py",
    "from game.replay_engine import GameplaySettingsSnapshot\n",
    '''from game.replay_engine import (\n    GameplaySettingsSnapshot,\n    parse_model_response,\n    resolve_shot,\n)\n''',
)
replace_once(
    "src/tests/test_trace_contract.py",
    '''    InvocationPolicy,\n    MediatedGameRuntime,\n    ScriptedClient,\n)\n''',
    '''    InvocationPolicy,\n    MediatedGameRuntime,\n    ScriptedClient,\n    extract_response_text,\n)\n''',
)
append_once(
    "src/tests/test_trace_contract.py",
    "def test_exact_response_text_is_preserved",
    '''def test_exact_response_text_is_preserved() -> None:
    assert extract_response_text("  M  ") == "  M  "


def test_command_grammar_rejects_suffixes_and_non_finite_numbers() -> None:
    for response in ("BLAH", "S10", "S01", "Mnan", "Minf", "Cnan", "Ainf"):
        parsed = parse_model_response(response)
        assert not parsed.valid
        assert parsed.normalized_cmd == "ERR"


def test_zero_bullet_step_is_safe() -> None:
    zero_step_rules = GameplaySettingsSnapshot.from_mapping(
        {**rules().to_dict(), "bullet_step_length": 0.0}
    )
    result = resolve_shot(initial_state(), 1, zero_step_rules)
    assert result.reason == "max_steps"
    assert result.path == []


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
''',
)

for path in (
    "research/urucon2026/paper/main.tex",
    "research/urucon2026/CLAIMS.md",
    "research/urucon2026/PAPER_REVIEW.md",
    "research/urucon2026/README.md",
):
    text = read(path)
    text = text.replace("application-level invocation object", "adapter-boundary invocation record")
    text = text.replace("adapter-boundary invocation object", "adapter-boundary invocation record")
    text = text.replace("object passed to the provider adapter", "record materialised at the provider-adapter boundary")
    write(path, text)
replace_once(
    "research/urucon2026/paper/main.tex",
    '''Here $a_i$ is the record materialised at the provider-adapter boundary: model name, endpoint declaration, ordered messages, options, and stream setting. It is not claimed to be the provider library's internal representation or the HTTP request emitted below that boundary.\n''',
    '''Here $a_i$ is the record materialised immediately before the provider-adapter call. Its model, ordered messages, options, and stream fields correspond to call arguments; provider and endpoint are application declarations. It is not the provider library's internal representation or the HTTP request emitted below that boundary.\n''',
)
replace_once(
    "research/urucon2026/paper/main.tex",
    "\\section*{Acknowledgment}",
    "\\section*{Acknowledgement}",
)
append_once(
    "research/urucon2026/AUDIT.md",
    "## Final hardening pass",
    '''## Final hardening pass

The final adversarial pass corrected additional defects that were not exposed by the initial deterministic corpus: permissive command-prefix parsing, acceptance of non-finite numeric commands, loss of response whitespace, a zero-length projectile-segment division, ambiguity when full text literally equalled the redaction marker, unsafe stringification of unknown event objects, canonical key collisions, incomplete cross-round continuity checks, and verifier exceptions on non-canonical values. Regression tests now cover each case. Public claims were also narrowed from an object purportedly passed wholesale to a provider adapter to an adapter-boundary record whose call-argument and declarative fields are distinguished explicitly.''',
)

print("Applied URUCON adversarial hardening fixes.")
