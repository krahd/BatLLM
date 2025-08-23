from __future__ import annotations
from typing import Dict, List, Optional


class PromptStore:
    """
    Store prompts per bot (identified by integer bot_id) plus a movable index
    pointing at the 'current' prompt for each bot.

    Internal record per bot_id:
        {"prompts": List[str], "index": int}
      - index starts at -1 (no current prompt)
    """

    def __init__(self) -> None:
        # bot_id -> {"prompts": [...], "index": int}
        self._data: Dict[int, Dict[str, object]] = {}

    # ---------------- Core API ----------------

    def add_prompt(self, id: int, prompt: str) -> int:
        """
        Add `prompt` to bot `id`'s list and set index to the new prompt.
        Creates the record if it doesn't exist.
        Returns the new index.
        """
        rec = self._data.setdefault(id, {"prompts": [], "index": -1})
        prompts: List[str] = rec["prompts"]  # type: ignore[assignment]
        prompts.append(prompt)
        rec["index"] = len(prompts) - 1
        return rec["index"]  # type: ignore[return-value]

    def rewind(self, id: int) -> Optional[str]:
        """
        Move the index one step back for bot `id`, if possible.
        Returns the new current prompt, or None if not possible (start or no data).
        """
        rec = self._data.get(id)
        if not rec:
            return None
        idx: int = rec["index"]  # type: ignore[assignment]
        prompts: List[str] = rec["prompts"]  # type: ignore[assignment]
        if idx - 1 >= 0:
            rec["index"] = idx - 1
            return prompts[rec["index"]]
        return None

    def forward(self, id: int) -> Optional[str]:
        """
        Move the index one step forward for bot `id`, if possible.
        Returns the new current prompt, or None if not possible (end or no data).
        """
        rec = self._data.get(id)
        if not rec:
            return None
        idx: int = rec["index"]  # type: ignore[assignment]
        prompts: List[str] = rec["prompts"]  # type: ignore[assignment]
        if idx + 1 < len(prompts):
            rec["index"] = idx + 1
            return prompts[rec["index"]]
        return None

    def reset(self, id: Optional[int] = None) -> None:
        """
        Reset prompts.
        - reset(id): delete all prompts for that bot and set index = -1
        - reset():   delete all prompts for all bots
        """
        if id is None:
            self._data.clear()
            return
        # Per-bot reset
        self._data[id] = {"prompts": [], "index": -1}

    def get_current_prompt(self, id: int) -> Optional[str]:
        """
        Return the prompt currently pointed by the index for bot `id`,
        or None if there is no current prompt.
        """
        rec = self._data.get(id)
        if not rec:
            return None
        idx: int = rec["index"]  # type: ignore[assignment]
        prompts: List[str] = rec["prompts"]  # type: ignore[assignment]
        if 0 <= idx < len(prompts):
            return prompts[idx]
        return None

    def get_index(self, id: int) -> int:
        """
        Return the current index for bot `id`.
        Returns -1 if the bot has no prompts or doesn't exist.
        """
        rec = self._data.get(id)
        if not rec:
            return -1
        return rec["index"]  # type: ignore[return-value]



    def toString(self) -> str:
        """
        Return a human-readable multi-line string summarizing all stored prompts.
        """

        if not self._data:
            return "PromptStore is empty."
        lines = []
        for bot_id, rec in self._data.items():
            idx: int = rec["index"]  # type: ignore[assignment]
            prompts: List[str] = rec["prompts"]  # type: ignore[assignment]
            lines.append(f"Bot {bot_id}: index={idx}, prompts={len(prompts)}")
            for i, p in enumerate(prompts):
                marker = " <==" if i == idx else ""
                lines.append(f"  [{i}] {p}{marker}")
        return "\n".join(lines)




    # ---------------- Optional: quick self-test ----------------
    @classmethod
    def _self_test(cls) -> None:
        ps = cls()
        assert ps.get_index(1) == -1 and ps.get_current_prompt(1) is None

        # add & current
        i0 = ps.add_prompt(1, "alpha")
        assert i0 == 0 and ps.get_current_prompt(1) == "alpha" and ps.get_index(1) == 0
        i1 = ps.add_prompt(1, "beta")
        assert i1 == 1 and ps.get_current_prompt(1) == "beta"

        # navigation
        assert ps.rewind(1) == "alpha"
        assert ps.rewind(1) is None  # at start
        assert ps.forward(1) == "beta"
        assert ps.forward(1) is None  # at end

        # second bot independent
        ps.add_prompt(2, "one")
        ps.add_prompt(2, "two")
        assert ps.get_current_prompt(2) == "two"
        assert ps.get_index(2) == 1

        # per-bot reset
        ps.reset(1)
        assert ps.get_index(1) == -1 and ps.get_current_prompt(1) is None
        assert ps.get_current_prompt(2) == "two"  # unaffected

        # global reset

        print("           **          PromptStore self-test: OK :)")
        return ps






if __name__ == "__main__":
    ps = PromptStore._self_test()
    print("_")
    print(ps.toString())
    print("__")
