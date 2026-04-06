"""Pure gameplay replay helpers shared by BatLLM and the analyzer."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Mapping

from configs.app_config import config


GAMEPLAY_SNAPSHOT_KEYS = (
    "bot_diameter",
    "bot_step_length",
    "bullet_damage",
    "bullet_diameter",
    "bullet_step_length",
    "shield_size",
    "shield_initial_state",
    "initial_health",
    "turns_per_round",
    "total_rounds",
)


def _to_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _to_int(value: Any, fallback: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _to_bool(value: Any, fallback: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "on"}:
            return True
        if lowered in {"false", "0", "no", "off"}:
            return False
    if value is None:
        return fallback
    return bool(value)


@dataclass(frozen=True)
class GameplaySettingsSnapshot:
    """Round-frozen gameplay settings required for deterministic replay."""

    bot_diameter: float
    bot_step_length: float
    bullet_damage: int
    bullet_diameter: float
    bullet_step_length: float
    shield_size: float
    shield_initial_state: bool
    initial_health: int
    turns_per_round: int
    total_rounds: int

    @classmethod
    def from_config(cls, cfg=config) -> "GameplaySettingsSnapshot":
        values = {
            key: cfg.get("game", key)
            for key in GAMEPLAY_SNAPSHOT_KEYS
        }
        return cls.from_mapping(values)

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any] | None) -> "GameplaySettingsSnapshot":
        values = values or {}
        return cls(
            bot_diameter=_to_float(values.get("bot_diameter"), 0.1),
            bot_step_length=_to_float(values.get("bot_step_length"), 0.03),
            bullet_damage=_to_int(values.get("bullet_damage"), 5),
            bullet_diameter=_to_float(values.get("bullet_diameter"), 0.02),
            bullet_step_length=_to_float(values.get("bullet_step_length"), 0.01),
            shield_size=_to_float(values.get("shield_size"), 70.0),
            shield_initial_state=_to_bool(values.get("shield_initial_state"), True),
            initial_health=_to_int(values.get("initial_health"), 30),
            turns_per_round=max(1, _to_int(values.get("turns_per_round"), 8)),
            total_rounds=max(1, _to_int(values.get("total_rounds"), 2)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "bot_diameter": self.bot_diameter,
            "bot_step_length": self.bot_step_length,
            "bullet_damage": self.bullet_damage,
            "bullet_diameter": self.bullet_diameter,
            "bullet_step_length": self.bullet_step_length,
            "shield_size": self.shield_size,
            "shield_initial_state": self.shield_initial_state,
            "initial_health": self.initial_health,
            "turns_per_round": self.turns_per_round,
            "total_rounds": self.total_rounds,
        }


@dataclass(frozen=True)
class ParsedCommand:
    raw_response: str
    normalized_cmd: str
    kind: str
    value: float | None = None
    valid: bool = True


@dataclass(frozen=True)
class ReplayEvent:
    type: str
    label: str
    bot_id: int | None = None
    target_bot_id: int | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ShotResolution:
    path: list[tuple[float, float]]
    damaged_bot_id: int | None = None
    blocked_bot_id: int | None = None
    reason: str = "none"


@dataclass(frozen=True)
class PlayResolution:
    bot_id: int
    llm_response: str
    normalized_cmd: str
    state_by_bot: dict[int, dict[str, Any]]
    events: list[ReplayEvent]
    shot_path: list[tuple[float, float]]


@dataclass(frozen=True)
class TurnReplay:
    initial_state: dict[int, dict[str, Any]]
    play_results: list[PlayResolution]
    final_state: dict[int, dict[str, Any]]
    mismatch: bool
    mismatch_details: list[str]


def normalize_state_map(state_map: Mapping[Any, Mapping[str, Any]] | None) -> dict[int, dict[str, Any]]:
    """Coerce history-manager state dictionaries into replay-friendly values."""
    normalized: dict[int, dict[str, Any]] = {}
    if not state_map:
        return normalized

    for key, value in state_map.items():
        bot_state = value or {}
        bot_id = _to_int(bot_state.get("id", key), _to_int(key))
        normalized[bot_id] = {
            "id": bot_id,
            "health": _to_int(bot_state.get("health"), 0),
            "x": _to_float(bot_state.get("x"), 0.0),
            "y": _to_float(bot_state.get("y"), 0.0),
            "rot": _to_float(bot_state.get("rot"), 0.0) % 360,
            "shield": _to_bool(bot_state.get("shield"), False),
            "current_prompt": str(bot_state.get("current_prompt", "")),
            "last_llm_response": bot_state.get("last_llm_response"),
        }
    return normalized


def clone_state_map(state_map: Mapping[int, Mapping[str, Any]]) -> dict[int, dict[str, Any]]:
    return {int(bot_id): dict(state) for bot_id, state in normalize_state_map(state_map).items()}


def clamp_position(x: float, y: float, *, radius: float) -> tuple[float, float]:
    return (
        min(max(x, radius), 1 - radius),
        min(max(y, radius), 1 - radius),
    )


def parse_model_response(response: Any) -> ParsedCommand:
    """Parse BatLLM command grammar into a normalized command."""
    raw = str(response or "").strip()
    if not raw:
        return ParsedCommand(raw_response=raw, normalized_cmd="ERR", kind="invalid", valid=False)

    head = raw[0].upper()
    if head == "M":
        if len(raw) == 1:
            return ParsedCommand(raw_response=raw, normalized_cmd="M", kind="move")
        try:
            distance = float(raw[1:])
        except ValueError:
            return ParsedCommand(raw_response=raw, normalized_cmd="ERR", kind="invalid", valid=False)
        return ParsedCommand(raw_response=raw, normalized_cmd=f"M{distance}", kind="move", value=distance)

    if head == "C":
        try:
            angle = float(raw[1:])
        except ValueError:
            return ParsedCommand(raw_response=raw, normalized_cmd="ERR", kind="invalid", valid=False)
        return ParsedCommand(raw_response=raw, normalized_cmd=f"C{angle}", kind="rotate_cw", value=angle)

    if head == "A":
        try:
            angle = float(raw[1:])
        except ValueError:
            return ParsedCommand(raw_response=raw, normalized_cmd="ERR", kind="invalid", valid=False)
        return ParsedCommand(raw_response=raw, normalized_cmd=f"A{angle}", kind="rotate_ccw", value=angle)

    if head == "B":
        return ParsedCommand(raw_response=raw, normalized_cmd="B", kind="shoot")

    if head == "S":
        if len(raw) == 1:
            return ParsedCommand(raw_response=raw, normalized_cmd="S", kind="shield_toggle")
        if raw[1] == "1":
            return ParsedCommand(raw_response=raw, normalized_cmd="S1", kind="shield_set", value=1.0)
        if raw[1] == "0":
            return ParsedCommand(raw_response=raw, normalized_cmd="S0", kind="shield_set", value=0.0)
        return ParsedCommand(raw_response=raw, normalized_cmd="ERR", kind="invalid", valid=False)

    return ParsedCommand(raw_response=raw, normalized_cmd="ERR", kind="invalid", valid=False)


def compute_move_target(state: Mapping[str, Any], rules: GameplaySettingsSnapshot, distance: float | None = None) -> tuple[float, float]:
    """Return the movement target for the given bot state."""
    step = rules.bot_step_length if distance is None else float(distance)
    rot = math.radians(_to_float(state.get("rot"), 0.0))
    x = _to_float(state.get("x"), 0.0) + math.cos(rot) * step
    y = _to_float(state.get("y"), 0.0) + math.sin(rot) * step
    radius = rules.bot_diameter / 2
    return clamp_position(x, y, radius=radius)


def compute_rotation_target(rot: float, delta: float) -> float:
    return (float(rot) + float(delta)) % 360


def _segment_interaction(
    target_state: Mapping[str, Any],
    p1: tuple[float, float],
    p2: tuple[float, float],
    rules: GameplaySettingsSnapshot,
) -> tuple[bool, bool]:
    """Return ``(hit, blocked)`` for the target and segment."""
    cx = _to_float(target_state.get("x"), 0.0)
    cy = _to_float(target_state.get("y"), 0.0)
    radius = rules.bot_diameter / 2

    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    fx = p1[0] - cx
    fy = p1[1] - cy
    a = dx**2 + dy**2
    b = 2 * (fx * dx + fy * dy)
    c = fx**2 + fy**2 - radius**2

    discriminant = b**2 - 4 * a * c
    if discriminant < 0:
        return False, False

    sqrt_disc = math.sqrt(discriminant)
    t_candidates = [
        (-b - sqrt_disc) / (2 * a),
        (-b + sqrt_disc) / (2 * a),
    ]
    hit_t = next((value for value in t_candidates if 0 <= value <= 1), None)
    if hit_t is None:
        return False, False

    if not _to_bool(target_state.get("shield"), False):
        return True, False

    hit_x = p1[0] + hit_t * dx
    hit_y = p1[1] + hit_t * dy
    impact_angle = math.atan2(hit_y - cy, hit_x - cx)
    shield_half_angle = math.radians(rules.shield_size + 18)
    diff = (impact_angle - math.radians(_to_float(target_state.get("rot"), 0.0)) +
            math.pi) % (2 * math.pi) - math.pi
    if abs(diff) <= shield_half_angle:
        return False, True
    return True, False


def resolve_shot(
    state_by_bot: Mapping[int, Mapping[str, Any]],
    actor_id: int,
    rules: GameplaySettingsSnapshot,
) -> ShotResolution:
    """Resolve a single shot using the shared logic model."""
    states = normalize_state_map(state_by_bot)
    actor = states.get(int(actor_id))
    if not actor or _to_bool(actor.get("shield"), False):
        return ShotResolution(path=[], reason="no_shot")

    x = _to_float(actor.get("x"), 0.0)
    y = _to_float(actor.get("y"), 0.0)
    rot = math.radians(_to_float(actor.get("rot"), 0.0))
    path: list[tuple[float, float]] = []
    shooter_radius = rules.bot_diameter / 2

    for _ in range(4096):
        if x < 0 or x > 1 or y < 0 or y > 1:
            return ShotResolution(path=path, reason="out_of_bounds")

        nx = x + rules.bullet_step_length * math.cos(rot)
        ny = y + rules.bullet_step_length * math.sin(rot)

        dist = math.dist((nx, ny), (actor["x"], actor["y"]))
        if dist * 0.97 > shooter_radius and 0 < nx < 1 and 0 < ny < 1:
            path.append((nx, ny))

        for other_id, target_state in states.items():
            if other_id == int(actor_id):
                continue
            hit, blocked = _segment_interaction(target_state, (x, y), (nx, ny), rules)
            if hit:
                return ShotResolution(path=path, damaged_bot_id=other_id, reason="hit")
            if blocked:
                return ShotResolution(path=path, blocked_bot_id=other_id, reason="shield_block")

        x, y = nx, ny

    return ShotResolution(path=path, reason="max_steps")


def apply_play(
    state_by_bot: Mapping[int, Mapping[str, Any]],
    *,
    bot_id: int,
    llm_response: str,
    cmd_text: str | None,
    rules: GameplaySettingsSnapshot,
) -> PlayResolution:
    """Apply one ordered play to a state map and return the new state."""
    states = clone_state_map(state_by_bot)
    actor_id = int(bot_id)
    actor = states.get(actor_id)
    normalized_source = cmd_text if cmd_text not in (None, "") else llm_response
    parsed = parse_model_response(normalized_source)

    if actor is None:
        return PlayResolution(
            bot_id=actor_id,
            llm_response=str(llm_response or ""),
            normalized_cmd="ERR",
            state_by_bot=states,
            events=[ReplayEvent(type="missing_bot", label="Missing bot", bot_id=actor_id)],
            shot_path=[],
        )

    events: list[ReplayEvent] = []
    shot_path: list[tuple[float, float]] = []
    if not parsed.valid:
        events.append(
            ReplayEvent(
                type="invalid_command",
                label="Invalid command",
                bot_id=actor_id,
                details={"raw_response": llm_response, "cmd": parsed.normalized_cmd},
            )
        )
        return PlayResolution(
            bot_id=actor_id,
            llm_response=str(llm_response or ""),
            normalized_cmd="ERR",
            state_by_bot=states,
            events=events,
            shot_path=shot_path,
        )

    if parsed.kind == "move":
        old_x = actor["x"]
        old_y = actor["y"]
        new_x, new_y = compute_move_target(actor, rules, parsed.value)
        actor["x"] = new_x
        actor["y"] = new_y
        event_type = "move" if not math.isclose(
            old_x, new_x) or not math.isclose(old_y, new_y) else "no_op"
        events.append(
            ReplayEvent(
                type=event_type,
                label=f"Move to ({new_x:.3f}, {new_y:.3f})" if event_type == "move" else "Move had no effect",
                bot_id=actor_id,
                details={"from": (old_x, old_y), "to": (new_x, new_y)},
            )
        )

    elif parsed.kind == "rotate_cw":
        old_rot = actor["rot"]
        actor["rot"] = compute_rotation_target(old_rot, parsed.value or 0.0)
        events.append(
            ReplayEvent(
                type="rotate",
                label=f"Rotate clockwise to {actor['rot']:.1f}d",
                bot_id=actor_id,
                details={"from": old_rot, "to": actor["rot"]},
            )
        )

    elif parsed.kind == "rotate_ccw":
        old_rot = actor["rot"]
        actor["rot"] = compute_rotation_target(old_rot, -(parsed.value or 0.0))
        events.append(
            ReplayEvent(
                type="rotate",
                label=f"Rotate counterclockwise to {actor['rot']:.1f}d",
                bot_id=actor_id,
                details={"from": old_rot, "to": actor["rot"]},
            )
        )

    elif parsed.kind == "shield_toggle":
        actor["shield"] = not _to_bool(actor.get("shield"), False)
        events.append(
            ReplayEvent(
                type="shield",
                label=f"Shield {'ON' if actor['shield'] else 'OFF'}",
                bot_id=actor_id,
                details={"value": actor["shield"]},
            )
        )

    elif parsed.kind == "shield_set":
        actor["shield"] = bool(parsed.value)
        events.append(
            ReplayEvent(
                type="shield",
                label=f"Shield {'ON' if actor['shield'] else 'OFF'}",
                bot_id=actor_id,
                details={"value": actor["shield"]},
            )
        )

    elif parsed.kind == "shoot":
        shot = resolve_shot(states, actor_id, rules)
        shot_path = list(shot.path)
        if shot.reason == "no_shot":
            events.append(
                ReplayEvent(
                    type="no_op",
                    label="Shot blocked because shield is ON",
                    bot_id=actor_id,
                )
            )
        else:
            events.append(
                ReplayEvent(
                    type="shot",
                    label="Shot fired",
                    bot_id=actor_id,
                    details={"path_length": len(shot_path)},
                )
            )
            if shot.blocked_bot_id is not None:
                events.append(
                    ReplayEvent(
                        type="shield_block",
                        label=f"Shield blocked Bot {actor_id}'s shot",
                        bot_id=actor_id,
                        target_bot_id=shot.blocked_bot_id,
                    )
                )
            if shot.damaged_bot_id is not None:
                target = states.get(int(shot.damaged_bot_id))
                if target is not None:
                    old_health = target["health"]
                    target["health"] = max(0, old_health - rules.bullet_damage)
                    events.append(
                        ReplayEvent(
                            type="damage",
                            label=f"Bot {shot.damaged_bot_id} took {rules.bullet_damage} damage",
                            bot_id=actor_id,
                            target_bot_id=shot.damaged_bot_id,
                            details={"from": old_health, "to": target["health"]},
                        )
                    )

    return PlayResolution(
        bot_id=actor_id,
        llm_response=str(llm_response or ""),
        normalized_cmd=parsed.normalized_cmd,
        state_by_bot=states,
        events=events,
        shot_path=shot_path,
    )


def compare_state_maps(
    derived: Mapping[int, Mapping[str, Any]],
    saved: Mapping[Any, Mapping[str, Any]] | None,
    *,
    tolerance: float = 1e-6,
) -> tuple[bool, list[str]]:
    """Compare two state maps with a small float tolerance."""
    saved_states = normalize_state_map(saved)
    derived_states = normalize_state_map(derived)
    details: list[str] = []
    bot_ids = sorted(set(saved_states) | set(derived_states))
    for bot_id in bot_ids:
        left = derived_states.get(bot_id)
        right = saved_states.get(bot_id)
        if left is None or right is None:
            details.append(f"Bot {bot_id} presence mismatch")
            continue
        for key in ("x", "y", "rot"):
            if not math.isclose(float(left[key]), float(right[key]), abs_tol=tolerance):
                details.append(f"Bot {bot_id} {key}: derived={left[key]!r} saved={right[key]!r}")
        for key in ("health", "shield"):
            if left[key] != right[key]:
                details.append(f"Bot {bot_id} {key}: derived={left[key]!r} saved={right[key]!r}")
    return (not details, details)


def replay_turn(
    pre_state: Mapping[Any, Mapping[str, Any]],
    plays: list[Mapping[str, Any]],
    rules: GameplaySettingsSnapshot,
    *,
    saved_post_state: Mapping[Any, Mapping[str, Any]] | None = None,
) -> TurnReplay:
    """Replay one turn from ordered plays."""
    current = normalize_state_map(pre_state)
    play_results: list[PlayResolution] = []
    for play in plays or []:
        bot_id = _to_int(play.get("bot_id"), 0)
        llm_response = str(play.get("llm_response", "") or "")
        cmd_text = str(play.get("cmd", "") or "")
        resolution = apply_play(
            current,
            bot_id=bot_id,
            llm_response=llm_response,
            cmd_text=cmd_text,
            rules=rules,
        )
        current = normalize_state_map(resolution.state_by_bot)
        play_results.append(resolution)

    matches, mismatch_details = compare_state_maps(current, saved_post_state)
    return TurnReplay(
        initial_state=normalize_state_map(pre_state),
        play_results=play_results,
        final_state=current,
        mismatch=not matches,
        mismatch_details=mismatch_details,
    )
