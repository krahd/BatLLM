"""
Ollama connector: manages chat requests and per-bot/shared message histories.

This connector targets Ollama's /api/chat contract. It does NOT use the deprecated
`context` field. Instead, it sends the whole `messages` list each call.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    # Only imported for type checking; won't run at runtime.
    from ollama._types import ChatResponse

from ollama import Client

from configs.app_config import config
from util.utils import _maybe_float, _maybe_int

Message = Dict[str, str]  # {"role": "system"|"user"|"assistant", "content": str}


class OllamaConnector:
    """
    Lean sync connector for Ollama.
    - Reuses one HTTP session
    - Tracks context per-bot or shared
    """

    def __init__(self) -> None:
        """Manage chat with an Ollama model using message histories (no KV `context`)."""

        # ---- Public knobs that UI may toggle live --------------------------------
        augmenting_prompt: bool
        independent_contexts: bool

        # ---- LLM options (read from config; some may be None) --------------------
        temperature: Optional[float]
        top_p: Optional[float]
        top_k: Optional[int]
        timeout: Optional[float]
        max_tokens: Optional[int]
        stop: Optional[Any]
        seed: Optional[int]
        num_thread: Optional[int]
        model: str
        num_ctx: Optional[int]
        num_predict: Optional[int]

        # ---- Internals ------------------------------------------------------------
        client: Optional[Client]
        _system_instructions: str
        _history_by_bot: Dict[int, List[Message]]
        _history_shared: List[Message]
        _max_history_messages: int  # simple, cheap cap (per history list)


    def __init__(self) -> None:
        # Defaults
        self.independent_contexts: bool = False
        self.augmenting_prompt: bool = False

        self.temperature = None
        self.top_p = None
        self.top_k = None
        self.timeout = None
        self.max_tokens = None
        self.stop = None
        self.seed = None
        self.num_thread = None
        self.model = ""
        self.num_ctx = None
        self.num_predict = None

        self.client = None
        self._system_instructions = ""
        self._history_by_bot = {}
        self._history_shared = []
        self._max_history_messages = int(config.get("llm", "max_history_messages")
                                         or config.get("game", "turns_per_round") * 2
                                         or 40)

        # Initial load
        self.load_options(force=True)


    def _ensure_system_message(self, history: List[Message]) -> None:
        """Ensure the system header (if any) is at messages[0]."""

        if self._system_instructions is None or not self._system_instructions.strip():
            # If we don't have system instructions we remove it from the history
            if history and history[0].get("role") == "system":
                del history[0]
            return

        if not history or history[0].get("role") != "system":
            history.insert(0, {"role": "system", "content": self._system_instructions})

        else:
            # keep it updated if file changed on disk and we reloaded
            if history[0].get("content") != self._system_instructions:
                history[0]["content"] = self._system_instructions



        print(f"** self._system_instructions = {self._system_instructions!r}")
        print(f"** history[0] = {history[0]!r}")
        print("")


    def reset_histories(self) -> None:
        """Drop all accumulated message histories."""
        self._history_by_bot.clear()
        self._history_shared.clear()  # type: ignore[attr-defined]



    def _build_user_message(self, *, game_state: Dict[str, Any], player_text: str) -> Message:
        """Build the user message content for the game mode

        Args:
            game_state (Dict[str, Any]): The state of the game as a dict
            player_text (str): The user prompt

        Returns:
            Message: The user message to send to the llm
        """

        if self.augmenting_prompt:
            # Compact JSON for token efficiency;
            content = f"[GAME_STATE]\n{json.dumps(game_state, separators=(",", ":"), ensure_ascii=False)}\n[PLAYER_INPUT]\n{player_text}"

        else:
            # if not augmenting then the message content is the user prompt as-is
            content = player_text

        return {"role": "user", "content": content}


    def _get_history_ref(self, bot_id: int) -> List[Message]:
        """Return a reference to the current history (a messages[] list), taking into account if the 
        context is shared or not"""

        if self.independent_contexts:
            lst = self._history_by_bot.get(bot_id)
            if lst is None:
                lst = []
                self._history_by_bot[bot_id] = lst
            return lst

        else:
            his = self._history_shared
            if self._history_shared is None:
                his = []
                self._history_shared = his
            return his




    def _trim_history_inplace(self, history: List[Message]) -> None:
        """Enforme maximum length of the history list in place.

        Policy:
          - Keep at most `_max_history_messages` entries.
          - ensure_system_message()
        """

        #  negative limit or None means no limit.
        if not self._max_history_messages or self._max_history_messages <= 0:
            return

        max_n = max(1, self._max_history_messages)

        if len(history) <= max_n:
            return


        tail = history[-max_n:]
        history.clear()
        history.extend(tail)
        self._ensure_system_message(history)

        # TODO verify this works OK



    def load_options(self, force: bool = False) -> None:
        """Load configuration and ensure client and contexts are consistent."""

        # Read from config (cast to proper types)
        self.temperature = _maybe_float(config.get("llm", "temperature"))
        self.top_p = _maybe_float(config.get("llm", "top_p"))
        self.top_k = _maybe_int(config.get("llm", "top_k"))

        self.timeout = config.get("llm", "timeout") or 55

        self.num_thread = _maybe_int(config.get("llm", "num_thread"))
        self.seed = _maybe_int(config.get("llm", "seed"))
        self.stop = _maybe_int(config.get("llm", "stop"))

        self.num_ctx = _maybe_int(config.get("llm", "num_ctx"))
        self.num_predict = _maybe_int(config.get("llm", "num_predict"))

        self.max_tokens = config.get("llm", "max_tokens") or None
        self.stop = config.get("llm", "stop") or None

        self.model = config.get("llm", "model")
        url = config.get("llm", "url")
        port = config.get("llm", "port")
        path = config.get("llm", "path")
        self.endpoint = f"{url}:{port}{path}"
        host = f"{url}:{port}"

        self._system_instructions = self._get_system_instructions_text()

        # Reset contexts when requested
        if force:
            self.reset_histories()

        # Client setup
        if self.client is None or force:
            self.client = Client(host=host, timeout=self.timeout)



    def process_settings(
        self,
        *,
        augmenting_prompt: Optional[bool] = None,
        independent_contexts: Optional[bool] = None,
        reset_histories_on_mode_change: bool = True,
    ) -> None:
        """updates the game options that are exposed to the user by the UI (settings), which are 
        passed as optional parameters to this method.

        if reset_histories_on_mode_change and the settings have changed then histories are reset
        """

        mode_changed = augmenting_prompt not in (
            None, self.augmenting_prompt) or independent_contexts not in (None, self.independent_contexts)

        self.augmenting_prompt = augmenting_prompt
        self.independent_contexts = independent_contexts

        # Reload system instructions
        self._system_instructions = self._get_system_instructions_text()

        # Histories from a prior mode might be not compatible with the new mode so we allow them to be reset them if the mode changed.
        if reset_histories_on_mode_change and mode_changed:
            self.reset_histories()


    def gen_options(self) -> Dict[str, Any]:
        """Refresh connector options and return generation options for chat."""

        # Load or refresh the options from the config and the UI
        self.load_options()

        res: Dict[str, Any] = {}

        if self.temperature is not None:
            res["temperature"] = self.temperature

        if self.top_p is not None:
            res["top_p"] = self.top_p

        if self.top_k is not None:
            res["top_k"] = self.top_k

        if self.max_tokens is not None:
            res["max_tokens"] = self.max_tokens

        if self.stop is not None:
            res["stop"] = self.stop

        if self.seed is not None:
            res["seed"] = self.seed

        if self.num_thread is not None:
            res["num_thread"] = self.num_thread

        if self.num_ctx is not None:
            res["num_ctx"] = self.num_ctx

        if self.num_predict is not None:
            res["num_predict"] = self.num_predict

        return res




    # Send message and return response
    def send_prompt_to_llm_sync(
        self,
        bot_id: int,
        *,
        user_text: str,
        game_state: dict[str, Any],
        reset: bool = False,
        new_augmenting_prompt: Optional[bool] = None,
        new_independent_contexts: Optional[bool] = None,

    ) -> str:
        """Send a synchronous chat request using message histories.

        Args:
            bot_id: The numeric ID of the bot (stable id).
            user_text: The *player* prompt
            game_state: JSON w/ current state                             
            reset: If True, reset the context (clear history) before sending.
            new_augmenting_prompt: If provided, update mode and reset history.
            new_independent_contexts:  If provided, update mode and reset history.

        Returns:
            The assistant's text content (single command if your header/player prompt enforces it).
        """


        self.process_settings(augmenting_prompt=new_augmenting_prompt,
                              independent_contexts=new_independent_contexts,
                              reset_histories_on_mode_change=True
                              )
        if reset:
            self.reset_histories()

        self.load_options()

        history = self._get_history_ref(bot_id)
        history.append(self._build_user_message(game_state=game_state, player_text=user_text))
        self._ensure_system_message(history)
        self._trim_history_inplace(history)


        # send the request
        res: "ChatResponse" = self.client.chat(
            model=self.model,
            messages=history,
            options=self.gen_options(),
            stream=False,
        )

        # ---- Extract assistant text ----
        content = ""

        # Preferred path: ChatResponse object
        try:
            # res.message is a ChatMessage; .content is the text
            content = (res.message.content or "").strip()  # type: ignore[attr-defined]


        except Exception:
            # Fallback for environments that return a dict

            if isinstance(res, dict):
                msg = res.get("message")

                if isinstance(msg, dict):
                    content = (msg.get("content") or "").strip()

                elif isinstance(res.get("response"), str):
                    content = (res["response"] or "").strip()

        if not content:
            # Helpful debug info without dumping the entire object
            typename = type(res).__name__
            raise RuntimeError(f"Empty or unparseable content from model (type={typename}).")

        # Persist llm reply into our history
        history.append({"role": "assistant", "content": content})

        # Optionally trim again if you enforce a hard cap:
        # self._trim_history_inplace(history)

        return content



    def _get_system_instructions_text(self) -> str:
        """Loads from assets/headers the header (system prompt) text for the LLM request based on the mode.

        Returns:
            str: _description_
        """
        # Determine the key based on the mode and context type (2x2 matrix)
        if not self.augmenting_prompt:
            key = ("system_instructions_not_augmented_independent" if self.independent_contexts else "system_instructions_not_augmented_shared")

        else:
            key = ("system_instructions_augmented_independent" if self.independent_contexts else "system_instructions_augmented_shared")

        # Get the path to the augmentation header text file from the config
        path = config.get("llm", key)

        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()

        except FileNotFoundError as exc:
            raise FileNotFoundError(f"System instructions file not found: {path}") from exc
