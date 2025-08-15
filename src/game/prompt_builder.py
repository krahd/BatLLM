# prompt_builder.py
# =================
#
# Centralized builders for BatLLM's LLM request payloads (schema v3.3).
#
# - Context:     shared vs independent
# - Augmentation: aug=True vs aug=False
#
# Key points
# ----------
# - Player prompts are constant within a round → included once as `round_prompt`.
# - History logs `llm_raw` (model output) and parsed `cmd` per play.
# - Augmented mode includes constants and single post-turn snapshots.
# - Independent+augmented includes BOTH bots' states, but only SELF plays appear in history.
# - Raises loudly if augmentation headers are required but missing, to avoid silent ambiguity.

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional
import json
import os

# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------


def _cfg_get(cfg: Any, section: str, key: str, default: Any = None) -> Any:
    """
    Robust getter for config-like objects (configparser or dicts).
    - configparser: cfg.get(section, key)
    - dict-of-dicts: cfg[section][key]
    - flat dict: cfg[f"{section}.{key}"]
    """
    if cfg is None:
        return default

    get = getattr(cfg, "get", None)
    if callable(get):
        try:
            return cfg.get(section, key)  # type: ignore[arg-type]
        except Exception:
            pass

    if isinstance(cfg, Mapping):
        sec = cfg.get(section)
        if isinstance(sec, Mapping) and key in sec:
            return sec.get(key, default)
        flat_key = f"{section}.{key}"
        if flat_key in cfg:
            return cfg.get(flat_key, default)

    return default


def _as_int(val: Any, default: int) -> int:
    try:
        return int(val)
    except Exception:
        return default


# ---------------------------------------------------------------------------
# Board/bot state extraction
# ---------------------------------------------------------------------------

def _bot_state_dict(bot_obj: Any) -> Dict[str, Any]:
    """
    Compact state dict with normalized arena assumptions and 0|1 shield.
    """
    def _g(attr: str, default=None):
        return getattr(bot_obj, attr, default)

    shield_val = _g("shield", 0)
    if isinstance(shield_val, bool):
        shield_val = 1 if shield_val else 0

    return {
        "x": _g("x", 0),             # normalized [0..1]
        "y": _g("y", 0),             # normalized [0..1]
        "rot": _g("rot", 0),         # degrees, >= 0
        "health": _g("health", 0),
        "shield": shield_val,        # 0|1
    }


def _get_self_and_opp(game_board: Any, self_bot: Any) -> tuple[Any, Any]:
    """
    Resolve (self, opp) bot objects from board. Falls back to the available list.
    """
    bots = getattr(game_board, "bots", []) or []
    if len(bots) >= 2:
        if self_bot in bots:
            opp = next((b for b in bots if b is not self_bot), bots[0])
            return self_bot, opp
        return bots[0], bots[1]
    return self_bot, self_bot


def _snapshot_from_board(game_board: Any, self_bot: Any) -> Dict[str, Dict[str, Any]]:
    """
    Prefer board.snapshot() if available; fallback to reading attributes.
    Board.snapshot() is expected to return {bot_id: {x,y,rot,health,shield}}
    """
    snap = getattr(game_board, "snapshot", None)
    if callable(snap):
        data = snap()
        if isinstance(data, Mapping) and data:
            self_id = getattr(self_bot, "id", None)
            if self_id is not None and self_id in data:
                opp_id = next((bid for bid in data.keys()
                              if bid != self_id), None)
                return {
                    "self": data.get(self_id, {}),
                    "opp": data.get(opp_id, {}) if opp_id is not None else {},
                }

    s_obj, o_obj = _get_self_and_opp(game_board, self_bot)
    return {"self": _bot_state_dict(s_obj), "opp": _bot_state_dict(o_obj)}


def _acting_order_string(game_board: Any, self_bot: Any) -> str:
    """
    "self_first" or "opp_first". Reads either:
      - game_board.current_round_order: [bot_id_first, bot_id_second]
      - game_board.shuffled_bots:      [obj_first, obj_second]
    Defaults to "self_first".
    """
    self_id = getattr(self_bot, "id", None)

    order_ids = getattr(game_board, "current_round_order", None)
    if isinstance(order_ids, (list, tuple)) and len(order_ids) == 2 and self_id is not None:
        return "self_first" if order_ids[0] == self_id else "opp_first"

    order_objs = getattr(game_board, "shuffled_bots", None)
    if isinstance(order_objs, (list, tuple)) and len(order_objs) == 2:
        first_id = getattr(order_objs[0], "id", None)
        if first_id is not None and self_id is not None:
            return "self_first" if first_id == self_id else "opp_first"

    return "self_first"


# ---------------------------------------------------------------------------
# Round prompts & history extraction
# ---------------------------------------------------------------------------

def _round_prompts(history_manager: Any, shared_context: bool, self_id: int) -> Dict[str, str]:
    """
    Reads the per-round prompts stored at round start.
    Expects: history_manager.current_round["prompts"] → [{"bot_id": int, "prompt": str}, ...]
    """
    out: Dict[str, str] = {}
    current_round = getattr(history_manager, "current_round", None)
    prompts = None
    if isinstance(current_round, Mapping):
        prompts = current_round.get("prompts")
    if not isinstance(prompts, list):
        return out

    if shared_context:
        for p in prompts:
            if not isinstance(p, Mapping):
                continue
            bid = int(p.get("bot_id", -1))
            txt = str(p.get("prompt", "")).strip()
            if not txt:
                continue
            if bid == self_id:
                out["self"] = txt
            else:
                out["opp"] = out.get("opp") or txt
    else:
        for p in prompts:
            if not isinstance(p, Mapping):
                continue
            bid = int(p.get("bot_id", -1))
            if bid == self_id:
                txt = str(p.get("prompt", "")).strip()
                if txt:
                    out["self"] = txt
                break

    return out


def _to_int_key_dict(d: Any) -> Dict[int, Any]:
    out: Dict[int, Any] = {}
    if isinstance(d, Mapping):
        for k, v in d.items():
            try:
                out[int(k)] = v
            except Exception:
                continue
    return out


def _build_history(history_manager: Any, shared_context: bool, self_id: int, augmented: bool) -> List[Dict[str, Any]]:
    """
    Builds the `history` list for the request body.

    - Always includes pre-recorded plays from HistoryManager.
    - Each entry: { "bot_id": int, "role": "assistant", "llm_raw": str, "cmd": str, "post_state": {...}? }
    - If shared_context=False, filter to only this bot's plays.
    - If augmented=True, include `post_state` per entry.
    """
    out: List[Dict[str, Any]] = []

    cur_round = getattr(history_manager, "current_round", None)
    if not isinstance(cur_round, Mapping):
        return out

    turns = cur_round.get("turns", [])
    if not isinstance(turns, list):
        return out

    for t in turns:
        if not isinstance(t, Mapping):
            continue
        messages = t.get("messages")
        if not isinstance(messages, list):
            continue

        post_state_map = t.get("post_state", {}) if augmented else {}
        post_state_by_bot = _to_int_key_dict(post_state_map)

        for m in messages:
            if not isinstance(m, Mapping):
                continue
            role = m.get("role")
            if role != "assistant":
                continue

            bot_id = m.get("bot_id")
            if not isinstance(bot_id, int):
                continue

            if (not shared_context) and bot_id != self_id:
                continue

            entry = {
                "bot_id": bot_id,
                "role": "assistant",
                "llm_raw": m.get("content", ""),
                "cmd": m.get("cmd", ""),
            }

            if augmented:
                ps = post_state_by_bot.get(bot_id)
                if isinstance(ps, Mapping):
                    entry["post_state"] = ps

            out.append(entry)

    return out


# ---------------------------------------------------------------------------
# Headers (augmented mode)
# ---------------------------------------------------------------------------

def _load_text_or_none(path: str) -> Optional[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def _load_system_header_or_crash(cfg: Any, shared_context: bool) -> str:
    """
    Returns the header text for augmented mode or raises RuntimeError
    if the configured file does not exist or cannot be read.
    """
    key = "augmentation_header_shared" if shared_context else "augmentation_header_independent"
    path = _cfg_get(cfg, "llm", key)
    if not isinstance(path, str) or not path.strip():
        raise RuntimeError(
            f"Augmented mode requires llm.{key} in config.yaml. Not found."
        )

    text = _load_text_or_none(path)
    if not isinstance(text, str) or not text.strip():
        raise RuntimeError(
            f"Augmented mode requires header file at '{path}', but it could not be read."
        )
    return text


# ---------------------------------------------------------------------------
# Public builder
# ---------------------------------------------------------------------------

class PromptBuilder:
    """
    Centralized construction of the /api/chat payload for Ollama.

    Usage:
        pb = PromptBuilder(history_manager, game_board, self_bot, app_config)
        data = pb.build_chat_payload(shared_context=True, augmented=True)

    This returns:
        {
          "model": "...",
          "options": { "num_ctx": ... },
          "messages": [
             {"role": "system", "content": "..."}?,      # only in augmented mode
             {"role": "user",   "content": "<JSON>"}      # main request body
          ]
        }
    """

    def __init__(self, history_manager: Any, game_board: Any, self_bot: Any, cfg: Any):
        self.hm = history_manager
        self.gb = game_board
        self.self_bot = self_bot
        self.cfg = cfg

    # --- top-level knobs from config ---
    @property
    def model(self) -> str:
        return str(_cfg_get(self.cfg, "llm", "model", "llama3.2:latest"))

    @property
    def num_ctx(self) -> int:
        return _as_int(_cfg_get(self.cfg, "llm", "num_ctx", 0), 0)

    # --- invariants / constants ---
    def _game_constants(self) -> Dict[str, Any]:
        g = _cfg_get(self.cfg, "game", "", {}) or _cfg_get(
            self.cfg, "game", "config", {})
        return {
            "STEP_LENGTH": _cfg_get(self.cfg, "game", "step_length", 0.02),
            "BULLET_DAMAGE": _cfg_get(self.cfg, "game", "bullet_damage", 5),
            "TOTAL_ROUNDS": _cfg_get(self.cfg, "game", "total_rounds", 1),
            "TURNS_PER_ROUND": _cfg_get(self.cfg, "game", "turns_per_round", 4),
        }

    # --- context block ---
    def _context_block(self, shared_context: bool) -> Dict[str, Any]:
        hm = self.hm
        gb = self.gb
        sb = self.self_bot

        # indices (1-based for human readability)
        round_idx = len(getattr(hm, "current_game", {}).get(
            "rounds", [])) + 0  # already in start_round()
        if isinstance(getattr(hm, "current_round", None), Mapping):
            round_idx = getattr(hm, "current_round").get("round", round_idx)

        turns = getattr(getattr(hm, "current_round", {}),
                        "get", lambda *a, **k: [])("turns", [])
        turn_idx = len(turns) + 0
        if isinstance(getattr(hm, "current_turn", None), Mapping):
            turn_idx = getattr(hm, "current_turn").get("turn", turn_idx)

        acting_order = _acting_order_string(gb, sb)
        prompts = _round_prompts(hm, shared_context, getattr(sb, "id", -1))

        return {
            "round_info": {
                "current_round": round_idx,
                "total_rounds": _cfg_get(self.cfg, "game", "total_rounds", 1),
            },
            "turn_info": {
                "current_turn": turn_idx,
                "turns_per_round": _cfg_get(self.cfg, "game", "turns_per_round", 4),
                "acting_order": acting_order,
            },
            "round_prompt": prompts,  # {"self": "...", "opp": "...?"}
        }

    # --- state block ---
    def _state_block(self, augmented: bool) -> Dict[str, Any]:
        if not augmented:
            return {}

        snap = _snapshot_from_board(self.gb, self.self_bot)
        # In augmented mode we include both initial round state and current pre-turn state
        initial_state = {}
        cur_round = getattr(self.hm, "current_round", None)
        if isinstance(cur_round, Mapping):
            initial_state = cur_round.get("initial_state") or {}

        pre_state = {}
        cur_turn = getattr(self.hm, "current_turn", None)
        if isinstance(cur_turn, Mapping):
            pre_state = cur_turn.get("pre_state") or {}
        if not pre_state:
            pre_state = snap  # fallback if needed

        return {
            "initial_state": initial_state,
            "pre_state": pre_state,
        }

    # --- history block ---
    def _history_block(self, shared_context: bool, augmented: bool) -> List[Dict[str, Any]]:
        return _build_history(self.hm, shared_context, getattr(self.self_bot, "id", -1), augmented)

    # --- final user JSON that goes into messages[role=user] ---
    def _build_user_payload(self, shared_context: bool, augmented: bool) -> Dict[str, Any]:
        body = {
            "meta": {
                "ctx_tokens": self.num_ctx or None,   # included only if non-zero
                "mode": {
                    "shared_context": bool(shared_context),
                    "augmented": bool(augmented),
                },
            },
            "context": self._context_block(shared_context),
            # {} if non-augmented
            "state": self._state_block(augmented),
            "history": self._history_block(shared_context, augmented),
        }

        # Drop None values recursively (keep the JSON tidy)
        def _clean(o):
            if isinstance(o, dict):
                return {k: _clean(v) for k, v in o.items() if v is not None}
            if isinstance(o, list):
                return [_clean(x) for x in o]
            return o

        return _clean(body)

    # --- public: messages + payload ---
    def build_chat_messages(self, shared_context: bool, augmented: bool) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = []

        if augmented:
            header_text = _load_system_header_or_crash(
                self.cfg, shared_context)
            messages.append({"role": "system", "content": header_text})

        user_json = self._build_user_payload(
            shared_context=shared_context, augmented=augmented)

        messages.append(
            {"role": "user", "content": json.dumps(user_json, ensure_ascii=False)})

        return messages

    def build_chat_payload(self, shared_context: bool, augmented: bool) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": self.build_chat_messages(shared_context=shared_context, augmented=augmented),
        }
        if self.num_ctx:
            payload["options"] = {"num_ctx": self.num_ctx}
        return payload
