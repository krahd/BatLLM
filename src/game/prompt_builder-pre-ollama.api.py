'''
prompt_builder.py
=================

Centralized builders for BatLLM's LLM request payloads.

This module produces the compact, stateless JSON body defined in the
"BatLLM Prompt JSON Specification (v3.2)", and (optionally) the complete
/messages payload for Ollama's /api/chat.

It supports the 2×2 matrix:

- Context:     shared vs independent
- Augmentation: aug=True vs aug=False

Key design points
-----------------
- Round prompts are constant within a round → included once in the body under
  `round_prompt` (not repeated per turn).
- History records both the model's raw output (`llm_raw`) and the parsed command
  (`cmd`) for each play.
- Augmented mode includes constants and state snapshots:
    - `const` (per game)
    - `initial_state`   (per round; first snapshot)
    - `current_state`   (state at the time of this request)
    - `history[*].post_state` (single post-turn snapshot per turn)
- Independent + augmented includes BOTH bots' states, but only SELF's plays in history.

Public API
----------
- build_batllm_body(...)
    Returns the dict body to be stringified and sent as a single `user` message.

- build_chat_messages(...)
    Returns the `messages` array for Ollama (/api/chat), adding a short
    system header when `aug=True`.

- build_chat_payload(...)
    Returns the full POST body for Ollama (/api/chat), including model, options,
    and messages.

All builders are defensive and won't crash if some optional fields do not exist
in your in-memory objects; they degrade gracefully to reasonable defaults.

Usage (typical)
---------------
    from prompt_builder import build_chat_payload

    payload = build_chat_payload(
        model="llama3.2:latest",
        num_ctx=32768,
        game_board=board_widget,
        history_manager=board_widget.history_manager,
        self_bot=my_bot,
        shared_context=True,      # False = independent
        augmented=True,           # False = non-augmented
        cfg=config,               # your config object/dict
        stream=False
    )
    # POST payload to Ollama: /api/chat

'''

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Tuple, Union
import json


# ---------------------------------------------------------------------------
# Helpers: robust config access
# ---------------------------------------------------------------------------

def _cfg_get(cfg: Any, section: str, key: str, default: Any = None) -> Any:
    """
    Return a config value for (section, key), handling both configparser-like
    objects and nested dicts. Falls back to `default` if missing.

    Supported shapes:
      - configparser: cfg.get(section, key)
      - dict-of-dicts: cfg[section][key]
      - flat dict: cfg[f"{section}.{key}"]

    Values are returned as-is (caller can coerce to int/float/bool).
    """
    if cfg is None:
        return default

    # configparser-like
    get = getattr(cfg, "get", None)
    if callable(get):
        try:
            return cfg.get(section, key)  # type: ignore[arg-type]
        except Exception:
            pass

    # dict-of-dicts
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
# Helpers: state extraction (defensive; adapts to your objects)
# ---------------------------------------------------------------------------

def _bot_label(bot_obj: Any, fallback_prefix: str = "BOT") -> str:
    """
    Return a human-friendly identifier for a bot. Prefers `name` then `id`.
    """
    name = getattr(bot_obj, "name", None)
    if isinstance(name, str) and name.strip():
        return name.strip()
    bot_id = getattr(bot_obj, "id", None)
    if bot_id is not None:
        return f"{fallback_prefix}{bot_id}"
    return f"{fallback_prefix}"


def _bot_state_dict(bot_obj: Any) -> Dict[str, Any]:
    """
    Extract a compact state dict from a bot object. Expected attributes:
      x, y, rot, health, shield (bool or 0/1)
    Missing attributes are defaulted conservatively.
    """
    def _g(attr: str, default=None):
        return getattr(bot_obj, attr, default)

    shield_val = _g("shield", 0)
    if isinstance(shield_val, bool):
        shield_val = 1 if shield_val else 0

    return {
        "x": _g("x", 0),
        "y": _g("y", 0),
        "rot": _g("rot", 0),
        "health": _g("health", 0),
        "shield": shield_val,
    }


def _get_bots(game_board: Any, self_bot: Any) -> Tuple[Any, Any]:
    """
    Return (self_obj, opp_obj) from the game_board and self_bot.
    Tries common shapes: game_board.bots (list of 2), or get_bot_by_id().
    """
    # Preferred: use explicit get_bot_by_id if present
    get_by_id = getattr(game_board, "get_bot_by_id", None)
    self_id = getattr(self_bot, "id", None)

    if callable(get_by_id) and self_id is not None:
        self_obj = get_by_id(self_id) or self_bot
        # naive opponent: assume two bots with ids 1 and 2 (or find "other" in bots list)
        other_id = 1 if self_id == 2 else 2
        opp_obj = get_by_id(other_id)
        if opp_obj is None:
            # Fallback: pick any bot that is not self
            bots_list = getattr(game_board, "bots", []) or []
            opp_obj = next((b for b in bots_list if getattr(b, "id", None) != self_id), None)
        return self_obj, (opp_obj or self_bot)

    # Fallback: bots list
    bots_list = getattr(game_board, "bots", []) or []
    if len(bots_list) >= 2:
        # Order: try to keep self first
        if self_bot in bots_list:
            opp = next((b for b in bots_list if b is not self_bot), bots_list[0])
            return self_bot, opp
        return bots_list[0], bots_list[1]

    # Last resort: duplicate self
    return self_bot, self_bot


def _state_snapshot(game_board: Any, self_bot: Any) -> Dict[str, Dict[str, Any]]:
    """
    Return {"self": {...}, "opp": {...}} snapshot from board.
    """
    s_obj, o_obj = _get_bots(game_board, self_bot)
    return {"self": _bot_state_dict(s_obj), "opp": _bot_state_dict(o_obj)}


def _acting_order_string(game_board: Any, self_bot: Any) -> str:
    """
    Determine acting order string for the current round.
    Tries, in order:
      - game_board.current_round_order: ["bot_id_first", "bot_id_second"]
      - game_board.shuffled_bots: [bot_obj_first, bot_obj_second]
    Falls back to "self_first".
    """
    self_id = getattr(self_bot, "id", None)

    # Option 1: explicit order as ids
    order_ids = getattr(game_board, "current_round_order", None)
    if isinstance(order_ids, (list, tuple)) and len(order_ids) == 2 and self_id is not None:
        return "self_first" if order_ids[0] == self_id else "opp_first"

    # Option 2: objects list
    order_objs = getattr(game_board, "shuffled_bots", None)
    if isinstance(order_objs, (list, tuple)) and len(order_objs) == 2:
        first = order_objs[0]
        first_id = getattr(first, "id", None)
        if first_id is not None and self_id is not None:
            return "self_first" if first_id == self_id else "opp_first"

    return "self_first"


# ---------------------------------------------------------------------------
# Helpers: prompts and history extraction
# ---------------------------------------------------------------------------

def _round_prompts(history_manager: Any, mode_shared: bool, self_id: int) -> Dict[str, str]:
    """
    Extract per-round, per-bot prompts that players entered at round start.
    Expected shapes:
      - history_manager.current_round["prompts"] == List[{"bot_id": int, "prompt": str}, ...]
    """
    out: Dict[str, str] = {}
    current_round = getattr(history_manager, "current_round", None)
    prompts = None
    if isinstance(current_round, Mapping):
        prompts = current_round.get("prompts")
    if not isinstance(prompts, list):
        return out

    if mode_shared:
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
    """
    Convert a dict with string/int keys to a dict with int keys (where possible).
    """
    out: Dict[int, Any] = {}
    if isinstance(d, Mapping):
        for k, v in d.items():
            try:
                out[int(k)] = v
            except Exception:
                continue
    return out


def _build_history(history_manager: Any, mode_shared: bool, self_id: int, aug: bool) -> List[Dict[str, Any]]:
    """
    Construct the history list for the request body.

    Expected shapes inside history_manager.current_round:
      - "turns": [
            {
              "turn": 1,
              "messages": [ {"bot_id": 1, "role": "assistant", "content": "C17"}, ... ],
              "parsed_commands": { 1: "C17", 2: "M" },
              "post_state": { 1: {...}, 2: {...} }   # when augmented
            },
            ...
        ]

    Rules:
      - shared: include plays for both bots; order inside a turn doesn't matter
      - independent: include plays for SELF only
      - augmented: include single post_state snapshot (both bots)
      - non-augmented: no post_state
    """
    result: List[Dict[str, Any]] = []
    current_round = getattr(history_manager, "current_round", None)
    turns = None
    if isinstance(current_round, Mapping):
        turns = current_round.get("turns")
    if not isinstance(turns, list):
        return result

    # Determine opponent id if available
    bot_ids_seen: set[int] = set()

    for trn in turns:
        if not isinstance(trn, Mapping):
            continue

        turn_index = int(trn.get("turn", 0)) or int(trn.get("turn_index", 0)) or 0

        # Collect assistant messages per bot (llm_raw)
        llm_raw_by_bot: Dict[int, str] = {}
        msgs = trn.get("messages") if isinstance(trn.get("messages"), list) else []
        for m in msgs:
            if not isinstance(m, Mapping):
                continue
            if str(m.get("role", "")).lower() != "assistant":
                continue
            bid = m.get("bot_id")
            try:
                bid = int(bid)
            except Exception:
                continue
            llm_raw_by_bot[bid] = str(m.get("content", "")).strip()
            bot_ids_seen.add(bid)

        parsed = _to_int_key_dict(trn.get("parsed_commands", {}) or {})
        for bid in parsed.keys():
            bot_ids_seen.add(bid)

        # Build plays
        plays: List[Dict[str, Any]] = []
        if mode_shared:
            # stable order: self first, then any other present
            other_ids = [b for b in sorted(bot_ids_seen) if b != self_id]
            ordered_ids = [self_id] + other_ids
            for bid in ordered_ids:
                if bid not in parsed and bid not in llm_raw_by_bot:
                    continue
                plays.append({
                    "bot": "self" if bid == self_id else "opp",
                    "llm_raw": llm_raw_by_bot.get(bid, ""),
                    "cmd": parsed.get(bid, "")
                })
        else:
            plays.append({
                "bot": "self",
                "llm_raw": llm_raw_by_bot.get(self_id, ""),
                "cmd": parsed.get(self_id, "")
            })

        entry: Dict[str, Any] = {"turn": turn_index, "plays": plays}

        if aug:
            post = trn.get("post_state", {})
            if isinstance(post, Mapping) and post:
                # Map numeric bot ids to roles
                post_int = _to_int_key_dict(post)
                # Try to infer opponent id quickly (assume 2-player)
                opp_id = next((bid for bid in post_int.keys() if bid != self_id), None)
                entry["post_state"] = {
                    "self": post_int.get(self_id, {}),
                    "opp": post_int.get(opp_id, {}) if opp_id is not None else {}
                }

        result.append(entry)

    return result


# ---------------------------------------------------------------------------
# Builders: body, messages, full payload
# ---------------------------------------------------------------------------

def build_batllm_body(
    *,
    game_board: Any,
    history_manager: Any,
    self_bot: Any,
    shared_context: bool,
    augmented: bool,
    cfg: Any
) -> Dict[str, Any]:
    """
    Build the BatLLM JSON body (schema v3.2) for a single /api/chat request.

    Parameters
    ----------
    game_board : object
        The live board widget/state. Expected attributes (best effort):
          - current_round (1-based), current_turn (1-based)
          - bots: list of bot objects (each with x,y,rot,health,shield,id,name)
          - current_round_order or shuffled_bots (optional) to infer acting order
    history_manager : object
        Provides structured round/turn/history data. Expects:
          - current_round dict with keys:
              - "prompts": [{'bot_id': int, 'prompt': str}, ...]
              - "turns": list of per-turn dicts (see _build_history docstring)
              - "initial_state" (optional)  {bot_id: state-dict}
    self_bot : object
        The bot object controlled by this request (has id/name/state fields).
    shared_context : bool
        When True, include both bots' plays/history and both prompts.
        When False (independent), include only SELF's plays and prompt.
    augmented : bool
        When True, include constants and state snapshots and add the system header.
        When False, exclude all state-related fields.
    cfg : config-like
        Game configuration. Supports configparser-like `.get(section, key)`
        and/or dict-like `cfg['section']['key']`.

    Returns
    -------
    dict
        A Python dict of the JSON body to be stringified and sent to the LLM.
    """
    # Derive ids and labels
    self_id = getattr(self_bot, "id", 1)
    self_label = _bot_label(self_bot)
    self_obj, opp_obj = _get_bots(game_board, self_bot)
    opp_label = _bot_label(opp_obj, fallback_prefix="OPP")

    # Round/turn indices (1-based)
    current_round = getattr(game_board, "current_round", 1) or 1
    current_turn = getattr(game_board, "current_turn", 1) or 1

    # Totals from config
    total_rounds = _as_int(_cfg_get(cfg, "game", "total_rounds", 1), 1)
    turns_per_round = _as_int(_cfg_get(cfg, "game", "turns_per_round", 1), 1)

    body: Dict[str, Any] = {
        "schema": "batllm.v3.2",
        "ctx": {"mode": "shared" if shared_context else "independent", "aug": augmented},
        "ids": {"self": self_label, "opp": opp_label},
        "round_info": {
            "current_round": current_round,
            "current_turn": current_turn,
            "total_rounds": total_rounds,
            "turns_per_round": turns_per_round,
            "acting_order": _acting_order_string(game_board, self_bot),
        },
        "round_prompt": _round_prompts(history_manager, shared_context, self_id),
        "history": _build_history(history_manager, shared_context, self_id, augmented),
    }

    if augmented:
        # Constants
        const = {
            "step_length": _as_int(_cfg_get(cfg, "game", "step_length", 50), 50),
            "bullet_damage": _as_int(_cfg_get(cfg, "game", "bullet_damage", 5), 5),
            "shield_degrees": _as_int(_cfg_get(cfg, "game", "shield_size", 64), 64),
            "initial_health": _as_int(_cfg_get(cfg, "game", "initial_health", 100), 100),
        }
        body["const"] = const

        # Round initial state (if HistoryManager recorded it; else snapshot)
        round_dict = getattr(history_manager, "current_round", None)
        initial_state = None
        if isinstance(round_dict, Mapping):
            # Accept either {bot_id: state} or {"self": {...}, "opp": {...}}
            is_map = round_dict.get("initial_state")
            if isinstance(is_map, Mapping):
                # Prefer role-labeled if present
                if "self" in is_map and "opp" in is_map:
                    initial_state = {"self": is_map["self"], "opp": is_map["opp"]}
                else:
                    # Map bot_id -> role
                    def _by_id(bid: int) -> Dict[str, Any]:
                        return is_map.get(bid, {})  # type: ignore[index]
                    other_id = 1 if self_id == 2 else 2
                    initial_state = {
                        "self": _by_id(self_id),
                        "opp": _by_id(other_id),
                    }
        if not isinstance(initial_state, Mapping):
            initial_state = _state_snapshot(game_board, self_bot)
        body["initial_state"] = initial_state

        # Current state snapshot (both bots; needed for planning/aim)
        body["current_state"] = _state_snapshot(game_board, self_bot)

    return body


def _default_system_header(bullet_damage: Optional[int] = None) -> str:
    """
    Build the short system header for augmented mode. If bullet_damage
    is provided, include the numeric value for clarity.
    """
    dmg = f"{bullet_damage}" if bullet_damage is not None else "BULLET_DAMAGE"
    return (
        "You control SELF in a two-bot arena. Output exactly one token:\n"
        "C{angle} | A{angle} | M | S1 | S0 | S | B\n"
        f"- B only fires if shield is down; a hit reduces target health by {dmg}.\n"
        "Any other text means “do nothing”."
    )


def build_chat_messages(
    *,
    game_board: Any,
    history_manager: Any,
    self_bot: Any,
    shared_context: bool,
    augmented: bool,
    cfg: Any,
    system_header: Optional[str] = None
) -> Tuple[List[Dict[str, str]], str]:
    """
    Build the `messages` array for Ollama /api/chat.

    Returns
    -------
    (messages, user_content_str)
        messages : list of dicts suitable for /api/chat
        user_content_str : compact JSON string of the user body (for logging)
    """
    body = build_batllm_body(
        game_board=game_board,
        history_manager=history_manager,
        self_bot=self_bot,
        shared_context=shared_context,
        augmented=augmented,
        cfg=cfg,
    )

    user_content = json.dumps(body, separators=(",", ":"))

    messages: List[Dict[str, str]] = []
    if augmented:
        if not system_header:
            # If we have bullet damage in cfg, include it for clarity
            bd = _as_int(_cfg_get(cfg, "game", "bullet_damage", None), None)  # type: ignore[arg-type]
            system_header = _default_system_header(bullet_damage=bd)
        messages.append({"role": "system", "content": system_header})

    messages.append({"role": "user", "content": user_content})
    return messages, user_content


def build_chat_payload(
    *,
    model: str,
    num_ctx: int,
    game_board: Any,
    history_manager: Any,
    self_bot: Any,
    shared_context: bool,
    augmented: bool,
    cfg: Any,
    stream: bool = False,
    temperature: Optional[float] = None,
    other_options: Optional[Dict[str, Any]] = None,
    system_header: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a ready-to-POST /api/chat payload for Ollama.

    Parameters
    ----------
    model : str
        Model identifier, e.g. "llama3.2:latest".
    num_ctx : int
        Context window to request (must not exceed model's capability).
    game_board, history_manager, self_bot, shared_context, augmented, cfg :
        As in build_chat_messages().
    stream : bool, default False
        Whether to stream tokens from Ollama (you likely want False for single-token commands).
    temperature : Optional[float]
        If provided, added to options.
    other_options : Optional[dict]
        Additional options to merge into the `options` dict (e.g., top_k, repeat_penalty).
    system_header : Optional[str]
        Override the system header (augmented=True only). If None, a default header is produced.

    Returns
    -------
    dict
        The full JSON payload for POST /api/chat.
    """
    messages, _ = build_chat_messages(
        game_board=game_board,
        history_manager=history_manager,
        self_bot=self_bot,
        shared_context=shared_context,
        augmented=augmented,
        cfg=cfg,
        system_header=system_header,
    )

    options: Dict[str, Any] = {"num_ctx": num_ctx}
    if temperature is not None:
        options["temperature"] = temperature
    if other_options:
        options.update(other_options)

    return {
        "model": model,
        "options": options,
        "messages": messages,
        "stream": stream,
    }


__all__ = [
    "build_batllm_body",
    "build_chat_messages",
    "build_chat_payload",
]
