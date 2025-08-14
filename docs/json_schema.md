![BatLLM's logo](./images/logo-small.png)
# 1: BatLLM Prompt JSON Specification (v3.2)

This document defines the **LLM request payload** used by BatLLM. It covers the 2×2 matrix of modes:
- **Context:** `shared` vs `independent`
- **Augmentation:** `aug=true` vs `aug=false`
    
The format aims to be compact, consistent, and stateless per call, including only the necessary data without spurious repetitions.


## 1.1:  Design goals

- **Clarity** for both humans and LLMs (explicit names, 1‑based counters).   
- **Performance**: one `user` JSON body (+ a short `system` header only when `aug=true`)    
- **No spurious repetition**: round prompts appear once per request; states appear only in augmented mode.    
- **Deterministic replay**: augmented history includes a **single post‑turn** snapshot per turn.    


## 1.2:  Versioning

- `schema`: fixed to `"batllm.v3.2"` in the payload body.
- Backward‑compatible additions should be introduced under new keys; avoid breaking changes. Changes to the schema that would break backward-compatibility should be merged in (minor) version changes.


## 1.3:  Envelope (messages sent to the LLM)

- **Augmented** (`aug=true`):    
    1. `system`: short game/command contract (see below)
    2. `user`: JSON body per the schema in this document        
       
- **Non‑augmented** (`aug=false`):
    1. `user`: JSON body only (no `system` message)

> Use a single `user` message with the entire JSON **stringified**.

### 1.3.1:  System Header Example (only when `aug=true`)

The actual header is loaded from the file specified in conf.yaml

```
You control SELF in a two-bot arena. Output exactly one token:
C{angle} | A{angle} | M | S1 | S0 | S | B
- B only fires if shield is down; a hit reduces target health by BULLET_DAMAGE.
Any other text means “do nothing”.
```



## 1.4:  Body schema (common fields)

MY_BOT and OPPONENT_BOT are identyifiers that might change. They are very ugly.

```json
{
  "schema": "batllm.v3.2",
  "ctx": { "mode": "shared|independent", "aug": true|false },

  "ids": { "self": "MY_BOT", "opp": "OPPONENT_BOT" },

  "round_info": {
    "current_round": 1,
    "current_turn": 3,
    "total_rounds": 3,
    "turns_per_round": 20,
    "acting_order": "self_first|opp_first"  
  },

  "round_prompt": {
    "self": "<player prompt for SELF (fixed for the round)>"
    /* in shared mode also include: "opp": "<opponent prompt>" */
  },

  /* present only when aug=true */
  "const": {
    "step_length": 50,
    "bullet_damage": 5,
    "shield_degrees": 64,
    "initial_health": 100
  },

  /* present only when aug=true */
  "initial_state": {
    "self": { "x": 20, "y": 30, "rot": 23, "health": 20, "shield": 1 },
    "opp":  { "x": 22, "y": 22, "rot": 22, "health": 21, "shield": 0 }
  },

  /* present only when aug=true (state at time of this request) */
  "current_state": {
    "self": { "x": 20, "y": 30, "rot": 23, "health": 20, "shield": 1 },
    "opp":  { "x": 22, "y": 22, "rot": 22, "health": 21, "shield": 0 }
  },

  "history": [
    {
      "turn": 1,
      "plays": [
        /* shared: two plays; independent: only self */
        { "bot": "self", "llm_raw": "S0",  "cmd": "S0" },
        { "bot": "opp",  "llm_raw": "S1",  "cmd": "S1" }
      ],
      /* present only when aug=true */
      "post_state": {
        "self": { "x": 20, "y": 30, "rot": 23, "health": 20, "shield": 0 },
        "opp":  { "x": 22, "y": 22, "rot": 22, "health": 21, "shield": 1 }
      }
    }
  ]
}
```

### 1.4.1:  Field notes

- `**ctx.mode**`
    
    - `shared`: include both prompts in `round_prompt` and two `plays` per turn.        
    - `independent`: include only `round_prompt.self`; `plays` contains only the SELF entry.  
        _Even in independent+augmented,_ `_initial_state_`_/_`_current_state_`_/_`_post_state_` _include both bots._
        
- `**round_prompt**`    
    - Appears **once** per request (constant for the round). Do **not** duplicate in each turn/play.
        
- `**history**`  
    - Each entry covers a turn. The order of plays inside a turn **does not matter** for the next decision (we rely on the single `post_state`).
    - Always record **both** `llm_raw` (exact model output) and parsed `cmd` (one-token command passed to the engine).        
    - In augmented mode, include a single `**post_state**` snapshot (both bots) after the two plays.
        
- `**const**`**,** `**initial_state**`**,** `**current_state**`**,** `**post_state**`
    - Present only when `aug=true`.        
    - `const` values are assumed fixed during a game but may change across games.
        



## 1.5:  Complete example (augmented=true, shared)

### 1.5.1:  messages payload to `/api/chat`

```json
{
  "model": "llama3.2:latest",
  "options": { "num_ctx": 32768 },
  "messages": [
    {
      "role": "system",
      "content": "You control SELF in a two-bot arena. Output exactly one token:\nC{angle} | A{angle} | M | S1 | S0 | S | B\n- B only fires if shield is down; a hit reduces target health by BULLET_DAMAGE.\nAny other text means \u201cdo nothing\u201d."
    },
    {
      "role": "user",
      "content": "{\"schema\":\"batllm.v3.2\",\"ctx\":{\"mode\":\"shared\",\"aug\":true},\"ids\":{\"self\":\"MY_BOT\",\"opp\":\"OPPONENT_BOT\"},\"round_info\":{\"current_round\":1,\"current_turn\":3,\"total_rounds\":3,\"turns_per_round\":20,\"acting_order\":\"self_first\"},\"round_prompt\":{\"self\":\"Close distance and shoot when shield is down.\",\"opp\":\"Keep distance and keep shield up; only move when threatened.\"},\"const\":{\"step_length\":50,\"bullet_damage\":5,\"shield_degrees\":64,\"initial_health\":100},\"initial_state\":{\"self\":{\"x\":20,\"y\":30,\"rot\":23,\"health\":20,\"shield\":1},\"opp\":{\"x\":22,\"y\":22,\"rot\":22,\"health\":21,\"shield\":0}},\"current_state\":{\"self\":{\"x\":20,\"y\":30,\"rot\":23,\"health\":20,\"shield\":1},\"opp\":{\"x\":22,\"y\":22,\"rot\":22,\"health\":21,\"shield\":0}},\"history\":[{\"turn\":1,\"plays\":[{\"bot\":\"self\",\"llm_raw\":\"S0\",\"cmd\":\"S0\"},{\"bot\":\"opp\",\"llm_raw\":\"S1\",\"cmd\":\"S1\"}],\"post_state\":{\"self\":{\"x\":20,\"y\":30,\"rot\":23,\"health\":20,\"shield\":0},\"opp\":{\"x\":22,\"y\":22,\"rot\":22,\"health\":21,\"shield\":1}}},{\"turn\":2,\"plays\":[{\"bot\":\"self\",\"llm_raw\":\"C17\",\"cmd\":\"C17\"},{\"bot\":\"opp\",\"llm_raw\":\"M\",\"cmd\":\"M\"}],\"post_state\":{\"self\":{\"x\":20,\"y\":30,\"rot\":40,\"health\":20,\"shield\":0},\"opp\":{\"x\":22,\"y\":72,\"rot\":22,\"health\":21,\"shield\":1}}}]}"
    }
  ],
  "stream": false
}
```



## 1.6:  Other variants (differences only)

- **augmented=true, independent**    
    - `round_prompt` contains only `self`        
    - `history[].plays` contains only the SELF entry        
    - States (`initial_state`, `current_state`, `post_state`) still include **both** bots
        
- **augmented=false, shared**    
    - Remove `const`, `initial_state`, `current_state`, and each `post_state`        
    - Keep two `plays` per history turn        
    - No system header
        
- **augmented=false, independent**    
    - As above, and `plays` contains only the SELF entry; `round_prompt` only `self`        
    
- s
- a.


# delete this after integration
## 1.7:  Implementation Notes



- Build the entire body as a Python dict and `json.dumps(..., separators=(",", ":"))` for compactness.    
- Persist per‑play logs with: `llm_raw`, `cmd`, and (if augmented) `post_state`. Round prompts are kept once per round.    
- Keep counters **1‑based** and consistently named: `current_round`, `current_turn`, `total_rounds`, `turns_per_round`.    
