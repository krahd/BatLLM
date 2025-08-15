'''
prompt_builder.py
=================

Centralized builders for BatLLM's LLM request payloads.

This module produces the compact, stateless JSON body defined in the
"BatLLM Prompt JSON Specification (v3.2)", and (optionally) the complete
/messages payload for Ollama's /api/chat.

It supports the different modes of BatLLM:
    - Shared Context vs Independent Context
    - Augmented Prompts vs Non-Augmented Prompts

Per BatLLM's game logic:

    - Round prompts are collected at round start, and are per-bot.
    - History records both the model's raw output (`llm_raw`) and resulting parsed command (`cmd`) for each play.
    
    - Augmented mode includes constants and state snapshots:        
        - `initial_state` state at round start (both bots)
        - `new_state` state after turn end (both bots)
        - `game_history` full history of rounds and plays, with both bots' actions of the current game.
        
    - Non-augmented mode excludes all state-related fields, and only includes the raw plays.
        
    - Independent Context + Augmented includes BOTH bots' states, but only SELF's plays in history.

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


Example Usage
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
