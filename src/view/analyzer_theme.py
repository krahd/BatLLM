"""Shared visual constants for the BatLLM Game Analyzer."""

from __future__ import annotations

from collections.abc import Iterable

SCREEN_BG = (0.94, 0.94, 0.92, 1.0)
PANEL_BG = (0.98, 0.98, 0.97, 1.0)
PANEL_ALT_BG = (0.88, 0.92, 0.99, 1.0)
PANEL_MUTED_BG = (0.93, 0.94, 0.96, 1.0)

TEXT_PRIMARY = (0.08, 0.08, 0.10, 1.0)
TEXT_SECONDARY = (0.24, 0.25, 0.30, 1.0)
TEXT_MUTED = (0.35, 0.36, 0.40, 1.0)
TEXT_INVERSE = (1.0, 1.0, 1.0, 1.0)

PRIMARY_BG = (0.30, 0.30, 0.40, 1.0)
PRIMARY_BG_ACTIVE = (0.24, 0.24, 0.33, 1.0)

SECONDARY_BG = (0.80, 0.88, 1.0, 1.0)
SECONDARY_BG_ACTIVE = (0.69, 0.75, 0.84, 1.0)

NEUTRAL_BG = (0.95, 0.95, 0.97, 1.0)
NEUTRAL_BG_ACTIVE = (0.88, 0.89, 0.93, 1.0)

ERROR_BG = (0.90, 0.61, 0.64, 1.0)
ERROR_BG_ACTIVE = (0.84, 0.50, 0.54, 1.0)
ERROR_TEXT = TEXT_INVERSE

SUCCESS_TEXT = (0.15, 0.35, 0.24, 1.0)
ERROR_TEXT_DARK = (0.55, 0.14, 0.14, 1.0)

TREE_DAMAGE_BG = (0.97, 0.88, 0.88, 1.0)
TREE_SHIELD_BG = (0.88, 0.94, 1.0, 1.0)
TREE_MISMATCH_BG = (0.96, 0.89, 0.96, 1.0)


def button_kwargs(role: str = "secondary") -> dict[str, tuple[float, float, float, float] | str]:
    """Return Kivy kwargs for explicitly themed buttons."""

    palette = {
        "primary": (PRIMARY_BG, TEXT_INVERSE),
        "secondary": (SECONDARY_BG, TEXT_PRIMARY),
        "neutral": (NEUTRAL_BG, TEXT_PRIMARY),
        "danger": (ERROR_BG, ERROR_TEXT),
    }
    background_color, text_color = palette.get(role, palette["secondary"])
    return {
        "background_normal": "",
        "background_down": "",
        "background_color": background_color,
        "color": text_color,
    }


def label_kwargs(*, muted: bool = False) -> dict[str, tuple[float, float, float, float]]:
    """Return Kivy kwargs for dynamically created labels."""

    return {"color": TEXT_MUTED if muted else TEXT_PRIMARY}


def tree_button_kwargs(
    kind: str,
    *,
    selected: bool = False,
    badge_tokens: Iterable[str] = (),
) -> dict[str, tuple[float, float, float, float] | str]:
    """Return themed button kwargs for analyzer session-tree rows."""

    badge_set = set(badge_tokens)
    background_color = PANEL_BG
    text_color = TEXT_PRIMARY

    if kind == "subheader":
        background_color = PANEL_ALT_BG
    elif "errors" in badge_set:
        background_color = ERROR_BG
        text_color = TEXT_INVERSE
    elif "damage" in badge_set:
        background_color = TREE_DAMAGE_BG
    elif "shield" in badge_set:
        background_color = TREE_SHIELD_BG
    elif "mismatch" in badge_set:
        background_color = TREE_MISMATCH_BG

    if selected:
        background_color = PRIMARY_BG
        text_color = TEXT_INVERSE

    return {
        "background_normal": "",
        "background_down": "",
        "background_color": background_color,
        "color": text_color,
    }
