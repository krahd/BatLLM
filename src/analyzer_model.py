"""Analyzer session/replay model used by the Game Analyzer UI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from game.replay_engine import GameplaySettingsSnapshot, ReplayEvent, TurnReplay, replay_turn


BOT_FILTER_BOTH = "Both"


def _as_int(value: Any, fallback: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


@dataclass(frozen=True)
class AnalyzerTreeRow:
    kind: str
    label: str
    game_index: int | None = None
    round_index: int | None = None
    flat_index: int | None = None
    badge_text: str = ""
    badge_tokens: tuple[str, ...] = ()


class AnalyzerSessionModel:
    """Stateful helper around a validated analyzer session payload."""

    def __init__(self, payload: dict[str, Any], source_path: str | Path):
        self.payload = payload
        self.source_path = Path(source_path)
        self.game_index = 0
        self.round_index = 0
        self.flat_index = 0
        self.bot_filter = BOT_FILTER_BOTH
        self._round_step_cache: dict[tuple[int, int], list[dict[str, Any]]] = {}

    @property
    def source_name(self) -> str:
        return self.source_path.name

    @property
    def games(self) -> list[dict[str, Any]]:
        return list(self.payload.get("games", []))

    def current_game(self) -> dict[str, Any]:
        return self.games[self.game_index]

    def current_round(self) -> dict[str, Any]:
        return self.current_game()["rounds"][self.round_index]

    def current_turns(self) -> list[dict[str, Any]]:
        return list(self.current_round().get("turns", []))

    def current_turn(self) -> dict[str, Any]:
        turns = self.current_turns()
        if not turns:
            return {}
        current_turn_index = self.current_entry()["turn_index"]
        return turns[current_turn_index]

    def game_labels(self) -> list[str]:
        return [f"Game {index + 1}" for index, _game in enumerate(self.games)]

    def round_labels(self) -> list[str]:
        return [
            f"Round {round_entry.get('round', index + 1)}"
            for index, round_entry in enumerate(self.current_game().get("rounds", []))
        ]

    def bot_filter_labels(self) -> list[str]:
        return [BOT_FILTER_BOTH, "Bot 1", "Bot 2"]

    def set_game_index(self, index: int) -> None:
        self.game_index = max(0, min(index, len(self.games) - 1))
        self.round_index = 0
        self.flat_index = 0

    def set_round_index(self, index: int) -> None:
        rounds = self.current_game().get("rounds", [])
        self.round_index = max(0, min(index, len(rounds) - 1))
        self.flat_index = 0

    def set_flat_index(self, index: int) -> None:
        steps = self.round_steps()
        if not steps:
            self.flat_index = 0
            return
        self.flat_index = max(0, min(index, len(steps) - 1))

    def set_bot_filter(self, value: str) -> None:
        self.bot_filter = value if value in self.bot_filter_labels() else BOT_FILTER_BOTH

    def step_count(self) -> int:
        return len(self.round_steps())

    def current_round_settings(self) -> dict[str, Any]:
        return dict(self.current_round().get("gameplay_settings_snapshot", {}))

    def current_turn_replay(self) -> TurnReplay | None:
        entry = self.current_entry()
        return entry.get("turn_replay")

    def current_entry(self) -> dict[str, Any]:
        steps = self.round_steps()
        if not steps:
            return {
                "label": "Round start",
                "turn_index": 0,
                "step_index": 0,
                "state_by_bot": self.current_round().get("initial_state", {}),
                "events": [],
                "shot_path": [],
                "turn_replay": None,
                "play": None,
                "badge_text": "",
            }
        return steps[self.flat_index]

    def round_steps(self) -> list[dict[str, Any]]:
        key = (self.game_index, self.round_index)
        cached = self._round_step_cache.get(key)
        if cached is not None:
            return cached

        round_entry = self.current_round()
        rules = GameplaySettingsSnapshot.from_mapping(round_entry.get("gameplay_settings_snapshot"))
        steps: list[dict[str, Any]] = []
        for turn_index, turn in enumerate(round_entry.get("turns", [])):
            replay = replay_turn(
                turn.get("pre_state", {}),
                turn.get("plays", []),
                rules,
                saved_post_state=turn.get("post_state", {}),
            )
            badge_parts: list[str] = []
            badge_tokens: list[str] = []
            if any(
                event.type == "damage"
                for resolution in replay.play_results
                for event in resolution.events
            ):
                badge_parts.append("[DMG]")
                badge_tokens.append("damage")
            if any(
                event.type == "invalid_command"
                for resolution in replay.play_results
                for event in resolution.events
            ):
                badge_parts.append("[ERR]")
                badge_tokens.append("errors")
            if any(
                event.type in {"shield", "shield_block"}
                for resolution in replay.play_results
                for event in resolution.events
            ):
                badge_parts.append("[SHD]")
                badge_tokens.append("shield")
            if replay.mismatch:
                badge_parts.append("[!]")
                badge_tokens.append("mismatch")
            badge_token_tuple = tuple(badge_tokens)

            steps.append(
                {
                    "label": f"Turn {turn.get('turn', turn_index + 1)} start",
                    "turn_index": turn_index,
                    "step_index": 0,
                    "state_by_bot": replay.initial_state,
                    "events": [ReplayEvent(type="turn_start", label="Turn start")],
                    "shot_path": [],
                    "turn_replay": replay,
                    "play": None,
                    "badge_text": "".join(badge_parts),
                    "badge_tokens": badge_token_tuple,
                }
            )
            for play_index, resolution in enumerate(replay.play_results, start=1):
                steps.append(
                    {
                        "label": f"Turn {turn.get('turn', turn_index + 1)} play {play_index}",
                        "turn_index": turn_index,
                        "step_index": play_index,
                        "state_by_bot": resolution.state_by_bot,
                        "events": resolution.events,
                        "shot_path": resolution.shot_path,
                        "turn_replay": replay,
                        "play": (turn.get("plays", []) or [])[play_index - 1],
                        "badge_text": "".join(badge_parts),
                        "badge_tokens": badge_token_tuple,
                    }
                )

        self._round_step_cache[key] = steps
        return steps

    def timeline_label(self) -> str:
        steps = self.round_steps()
        if not steps:
            return "No replay steps."
        labels = []
        for index, step in enumerate(steps):
            marker = ">" if index == self.flat_index else "-"
            labels.append(f"{marker}T{step['turn_index'] + 1}:{step['step_index']}")
        return " ".join(labels)

    def current_bot_states(self) -> list[dict[str, Any]]:
        state_by_bot = self.current_entry().get("state_by_bot", {})
        filtered = []
        for bot_id in sorted(int(key) for key in state_by_bot):
            state = state_by_bot[bot_id]
            if self.bot_filter == "Bot 1" and bot_id != 1:
                continue
            if self.bot_filter == "Bot 2" and bot_id != 2:
                continue
            filtered.append(state)
        return filtered

    def format_prompts(self) -> str:
        prompts = self.current_round().get("prompts", [])
        lines = []
        for prompt in prompts:
            bot_id = _as_int(prompt.get("bot_id"), 0)
            if self.bot_filter == "Bot 1" and bot_id != 1:
                continue
            if self.bot_filter == "Bot 2" and bot_id != 2:
                continue
            lines.append(f"[b]Bot {bot_id}[/b]\n{prompt.get('prompt', '')}\n")
        return "\n".join(lines).strip() or "No prompts recorded."

    def format_plays(self) -> str:
        turn = self.current_turn()
        if not turn:
            return "No plays recorded."
        current_step = self.current_entry().get("step_index", 0)
        lines = []
        for play_index, play in enumerate(turn.get("plays", []), start=1):
            bot_id = _as_int(play.get("bot_id"), 0)
            if self.bot_filter == "Bot 1" and bot_id != 1:
                continue
            if self.bot_filter == "Bot 2" and bot_id != 2:
                continue
            prefix = "[b]>[/b] " if play_index == current_step else "  "
            lines.append(
                f"{prefix}[b]Bot {bot_id}[/b] llm={play.get('llm_response', '')!r} cmd={play.get('cmd', '')}"
            )
        return "\n".join(lines).strip() or "No plays for this filter."

    def format_state_diff(self) -> str:
        entry = self.current_entry()
        step_index = entry.get("step_index", 0)
        if step_index == 0:
            return "Turn start. No state diff yet."

        turn_replay = entry.get("turn_replay")
        if turn_replay is None:
            return "No replay state."

        previous_state = (
            turn_replay.initial_state
            if step_index == 1
            else turn_replay.play_results[step_index - 2].state_by_bot
        )
        current_state = entry.get("state_by_bot", {})

        lines = []
        for bot_id in sorted(int(key) for key in current_state):
            if self.bot_filter == "Bot 1" and bot_id != 1:
                continue
            if self.bot_filter == "Bot 2" and bot_id != 2:
                continue
            before = previous_state.get(bot_id, {})
            after = current_state.get(bot_id, {})
            changed = []
            for key in ("x", "y", "rot", "health", "shield"):
                if before.get(key) != after.get(key):
                    changed.append(f"{key}: {before.get(key)!r} -> {after.get(key)!r}")
            if changed:
                lines.append(f"[b]Bot {bot_id}[/b]\n" + "\n".join(changed))
        return "\n\n".join(lines).strip() or "No state changes."

    def format_round_settings(self) -> str:
        settings = self.current_round_settings()
        order = (
            "bot_diameter",
            "bot_step_length",
            "bullet_damage",
            "bullet_step_length",
            "shield_size",
            "shield_initial_state",
            "initial_health",
            "turns_per_round",
            "total_rounds",
        )
        return "\n".join(f"[b]{key}[/b]: {settings.get(key)!r}" for key in order)

    def format_insights(self) -> str:
        entry = self.current_entry()
        lines = [event.label for event in entry.get("events", [])]
        replay = entry.get("turn_replay")
        if replay and replay.mismatch:
            lines.append("[b]Replay mismatch detected[/b]")
            lines.extend(replay.mismatch_details)
        return "\n".join(lines).strip() or "No insights for this step."

    def session_tree_rows(self) -> list[AnalyzerTreeRow]:
        original_game_index = self.game_index
        original_round_index = self.round_index
        original_flat_index = self.flat_index
        rows: list[AnalyzerTreeRow] = []
        for game_index, game in enumerate(self.games):
            rows.append(AnalyzerTreeRow(kind="header", label=f"Game {game_index + 1}"))
            for round_index, round_entry in enumerate(game.get("rounds", [])):
                rows.append(
                    AnalyzerTreeRow(
                        kind="subheader",
                        label=f"Round {round_entry.get('round', round_index + 1)}",
                        game_index=game_index,
                        round_index=round_index,
                        flat_index=0,
                    )
                )
                if (game_index, round_index) not in self._round_step_cache:
                    self.set_game_index(game_index)
                    self.set_round_index(round_index)
                    self.round_steps()
                for step_index, step in enumerate(self._round_step_cache[(game_index, round_index)]):
                    if step["step_index"] != 0:
                        continue
                    rows.append(
                        AnalyzerTreeRow(
                            kind="turn",
                            label=step["label"],
                            game_index=game_index,
                            round_index=round_index,
                            flat_index=step_index,
                            badge_text=step["badge_text"],
                            badge_tokens=tuple(step.get("badge_tokens", ())),
                        )
                    )
        self.set_game_index(original_game_index)
        self.set_round_index(original_round_index)
        self.set_flat_index(original_flat_index)
        return rows
