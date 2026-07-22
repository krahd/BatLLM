"""Independent reference semantics for BatLLM's bounded command language.

This module intentionally imports no BatLLM gameplay code. The differential
experiment uses it as a separately implemented executable specification for
normalisation, state transition, and semantic events.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping


@dataclass(frozen=True)
class ReferenceRules:
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
    def from_mapping(cls, values: Mapping[str, Any]) -> "ReferenceRules":
        return cls(
            bot_diameter=float(values["bot_diameter"]),
            bot_step_length=float(values["bot_step_length"]),
            bullet_damage=int(values["bullet_damage"]),
            bullet_diameter=float(values["bullet_diameter"]),
            bullet_step_length=float(values["bullet_step_length"]),
            shield_size=float(values["shield_size"]),
            shield_initial_state=bool(values["shield_initial_state"]),
            initial_health=int(values["initial_health"]),
            turns_per_round=int(values["turns_per_round"]),
            total_rounds=int(values["total_rounds"]),
        )


@dataclass(frozen=True)
class ReferenceCommand:
    normalized: str
    kind: str
    value: float | None = None
    valid: bool = True


@dataclass(frozen=True)
class ReferenceResolution:
    normalized_command: str
    state_by_bot: dict[int, dict[str, Any]]
    events: list[dict[str, Any]]
    shot_path: list[tuple[float, float]]


def _float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _int(value: Any, fallback: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _bool(value: Any, fallback: bool = False) -> bool:
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


def normalize_state(
    state_map: Mapping[Any, Mapping[str, Any]] | None,
) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for key, value in (state_map or {}).items():
        state = value or {}
        bot_id = _int(state.get("id", key), _int(key))
        result[bot_id] = {
            "id": bot_id,
            "health": _int(state.get("health"), 0),
            "x": _float(state.get("x"), 0.0),
            "y": _float(state.get("y"), 0.0),
            "rot": _float(state.get("rot"), 0.0) % 360,
            "shield": _bool(state.get("shield"), False),
            "current_prompt": str(state.get("current_prompt", "")),
            "last_llm_response": state.get("last_llm_response"),
        }
    return result


def _parse_finite_number(fragment: str) -> float | None:
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
    return ReferenceCommand("ERR", "invalid", valid=False)


def _event(
    event_type: str,
    label: str,
    *,
    bot_id: int | None = None,
    target_bot_id: int | None = None,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "type": event_type,
        "label": label,
        "bot_id": bot_id,
        "target_bot_id": target_bot_id,
        "details": dict(details or {}),
    }


def _clamp(value: float, radius: float) -> float:
    return min(max(value, radius), 1.0 - radius)


def _segment_interaction(
    target: Mapping[str, Any],
    p1: tuple[float, float],
    p2: tuple[float, float],
    rules: ReferenceRules,
) -> tuple[bool, bool]:
    cx = _float(target.get("x"))
    cy = _float(target.get("y"))
    radius = rules.bot_diameter / 2.0
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    fx = p1[0] - cx
    fy = p1[1] - cy
    a = dx * dx + dy * dy
    if a == 0:
        return False, False
    b = 2.0 * (fx * dx + fy * dy)
    c = fx * fx + fy * fy - radius * radius
    discriminant = b * b - 4.0 * a * c
    if discriminant < 0:
        return False, False
    root = math.sqrt(discriminant)
    candidates = [(-b - root) / (2.0 * a), (-b + root) / (2.0 * a)]
    hit_t = next((candidate for candidate in candidates if 0 <= candidate <= 1), None)
    if hit_t is None:
        return False, False
    if not _bool(target.get("shield"), False):
        return True, False
    hit_x = p1[0] + hit_t * dx
    hit_y = p1[1] + hit_t * dy
    impact_angle = math.atan2(hit_y - cy, hit_x - cx)
    shield_half_angle = math.radians(rules.shield_size + 18.0)
    difference = (
        impact_angle - math.radians(_float(target.get("rot"))) + math.pi
    ) % (2.0 * math.pi) - math.pi
    if abs(difference) <= shield_half_angle:
        return False, True
    return True, False


def _resolve_shot(
    states: Mapping[int, Mapping[str, Any]],
    actor_id: int,
    rules: ReferenceRules,
) -> tuple[list[tuple[float, float]], int | None, int | None, str]:
    actor = states.get(actor_id)
    if actor is None or _bool(actor.get("shield"), False):
        return [], None, None, "no_shot"
    x = _float(actor.get("x"))
    y = _float(actor.get("y"))
    rotation = math.radians(_float(actor.get("rot")))
    path: list[tuple[float, float]] = []
    shooter_radius = rules.bot_diameter / 2.0
    for _ in range(4096):
        if x < 0 or x > 1 or y < 0 or y > 1:
            return path, None, None, "out_of_bounds"
        nx = x + rules.bullet_step_length * math.cos(rotation)
        ny = y + rules.bullet_step_length * math.sin(rotation)
        distance = math.dist((nx, ny), (_float(actor["x"]), _float(actor["y"])))
        if distance * 0.97 > shooter_radius and 0 < nx < 1 and 0 < ny < 1:
            path.append((nx, ny))
        for other_id, target in states.items():
            if other_id == actor_id:
                continue
            hit, blocked = _segment_interaction(target, (x, y), (nx, ny), rules)
            if hit:
                return path, other_id, None, "hit"
            if blocked:
                return path, None, other_id, "shield_block"
        x, y = nx, ny
    return path, None, None, "max_steps"


def apply_reference(
    state_by_bot: Mapping[Any, Mapping[str, Any]],
    *,
    bot_id: int,
    response: str,
    rules: ReferenceRules,
) -> ReferenceResolution:
    states = normalize_state(state_by_bot)
    actor_id = int(bot_id)
    actor = states.get(actor_id)
    parsed = parse_command(response)
    if actor is None:
        return ReferenceResolution(
            normalized_command="ERR",
            state_by_bot=states,
            events=[_event("missing_bot", "Missing bot", bot_id=actor_id)],
            shot_path=[],
        )
    if not parsed.valid:
        return ReferenceResolution(
            normalized_command="ERR",
            state_by_bot=states,
            events=[
                _event(
                    "invalid_command",
                    "Invalid command",
                    bot_id=actor_id,
                    details={"cmd": "ERR"},
                )
            ],
            shot_path=[],
        )

    events: list[dict[str, Any]] = []
    shot_path: list[tuple[float, float]] = []
    if parsed.kind == "move":
        old_x, old_y = actor["x"], actor["y"]
        step = rules.bot_step_length if parsed.value is None else float(parsed.value)
        rotation = math.radians(_float(actor.get("rot")))
        radius = rules.bot_diameter / 2.0
        new_x = _clamp(old_x + math.cos(rotation) * step, radius)
        new_y = _clamp(old_y + math.sin(rotation) * step, radius)
        actor["x"], actor["y"] = new_x, new_y
        changed = not math.isclose(old_x, new_x) or not math.isclose(old_y, new_y)
        event_type = "move" if changed else "no_op"
        label = (
            f"Move to ({new_x:.3f}, {new_y:.3f})"
            if changed
            else "Move had no effect"
        )
        events.append(
            _event(
                event_type,
                label,
                bot_id=actor_id,
                details={"from": (old_x, old_y), "to": (new_x, new_y)},
            )
        )
    elif parsed.kind == "rotate_cw":
        old = actor["rot"]
        actor["rot"] = (float(old) + float(parsed.value or 0.0)) % 360.0
        events.append(
            _event(
                "rotate",
                f"Rotate clockwise to {actor['rot']:.1f}d",
                bot_id=actor_id,
                details={"from": old, "to": actor["rot"]},
            )
        )
    elif parsed.kind == "rotate_ccw":
        old = actor["rot"]
        actor["rot"] = (float(old) - float(parsed.value or 0.0)) % 360.0
        events.append(
            _event(
                "rotate",
                f"Rotate counterclockwise to {actor['rot']:.1f}d",
                bot_id=actor_id,
                details={"from": old, "to": actor["rot"]},
            )
        )
    elif parsed.kind == "shield_toggle":
        actor["shield"] = not _bool(actor.get("shield"), False)
        events.append(
            _event(
                "shield",
                f"Shield {'ON' if actor['shield'] else 'OFF'}",
                bot_id=actor_id,
                details={"value": actor["shield"]},
            )
        )
    elif parsed.kind == "shield_set":
        actor["shield"] = bool(parsed.value)
        events.append(
            _event(
                "shield",
                f"Shield {'ON' if actor['shield'] else 'OFF'}",
                bot_id=actor_id,
                details={"value": actor["shield"]},
            )
        )
    elif parsed.kind == "shoot":
        shot_path, damaged, blocked, reason = _resolve_shot(states, actor_id, rules)
        if reason == "no_shot":
            events.append(
                _event(
                    "no_op",
                    "Shot blocked because shield is ON",
                    bot_id=actor_id,
                )
            )
        else:
            events.append(
                _event(
                    "shot",
                    "Shot fired",
                    bot_id=actor_id,
                    details={"path_length": len(shot_path)},
                )
            )
            if blocked is not None:
                events.append(
                    _event(
                        "shield_block",
                        f"Shield blocked Bot {actor_id}'s shot",
                        bot_id=actor_id,
                        target_bot_id=blocked,
                    )
                )
            if damaged is not None:
                target = states.get(damaged)
                if target is not None:
                    old_health = target["health"]
                    target["health"] = max(0, old_health - rules.bullet_damage)
                    events.append(
                        _event(
                            "damage",
                            f"Bot {damaged} took {rules.bullet_damage} damage",
                            bot_id=actor_id,
                            target_bot_id=damaged,
                            details={"from": old_health, "to": target["health"]},
                        )
                    )
    return ReferenceResolution(parsed.normalized, states, events, shot_path)


def states_equivalent(
    left: Mapping[Any, Mapping[str, Any]],
    right: Mapping[Any, Mapping[str, Any]],
    *,
    tolerance: float = 1e-9,
) -> bool:
    left_states = normalize_state(left)
    right_states = normalize_state(right)
    if set(left_states) != set(right_states):
        return False
    for bot_id in left_states:
        a, b = left_states[bot_id], right_states[bot_id]
        for key in ("x", "y", "rot"):
            if not math.isclose(float(a[key]), float(b[key]), abs_tol=tolerance):
                return False
        for key in ("health", "shield"):
            if a[key] != b[key]:
                return False
    return True


def paths_equivalent(
    left: list[tuple[float, float]],
    right: list[tuple[float, float]],
    *,
    tolerance: float = 1e-9,
) -> bool:
    return len(left) == len(right) and all(
        math.isclose(ax, bx, abs_tol=tolerance)
        and math.isclose(ay, by, abs_tol=tolerance)
        for (ax, ay), (bx, by) in zip(left, right)
    )
