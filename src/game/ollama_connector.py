"""
Ollama connector: manages chat requests and per-bot/shared message histories.

This connector targets Ollama's /api/chat contract. It does NOT use the deprecated
`context` field. Instead, it sends the whole `messages` list each call.
"""

from __future__ import annotations
from util.utils import _maybe_float, _maybe_int
from util.paths import resolve_repo_relative
from configs.app_config import config
from llm import service as ollama_service

import json

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Dict, List, Optional

try:
    import httpcore
except ImportError:  # pragma: no cover - dependency is normally present via ollama/httpx
    httpcore = None

try:
    import httpx
except ImportError:  # pragma: no cover - dependency is normally present via ollama/httpx
    httpx = None

if TYPE_CHECKING:
    # Only imported for type checking; won't run at runtime.
    from ollama._types import ChatResponse

from llm.adapter import get_client

# Compatibility: previous code imported `Client` from the `ollama` package
# and many tests monkeypatch `game.ollama_connector.Client`. Provide a
# `Client` symbol that mirrors the previous constructor API (callable
# returning an object with `.chat(...)`).
Client = get_client


Message = Dict[str, str]  # {"role": "system"|"user"|"assistant", "content": str}


TIMEOUT_EXCEPTIONS: tuple[type[BaseException], ...] = (TimeoutError,)
if httpx is not None:
    TIMEOUT_EXCEPTIONS += (httpx.TimeoutException,)
if httpcore is not None:
    TIMEOUT_EXCEPTIONS += (httpcore.TimeoutException,)


class LLMTimeoutError(RuntimeError):
    """Raised when Ollama times out even after a retry."""

    def __init__(
        self,
        *,
        model: str,
        timeout: float | None,
        attempts: int,
        original_exception: BaseException,
    ) -> None:
        self.model = model
        normalized_timeout = _maybe_float(timeout) if timeout is not None else None
        self.timeout = normalized_timeout if normalized_timeout is not None else timeout
        self.attempts = attempts
        self.original_exception = original_exception
        try:
            timeout_suffix = f" after {self.timeout:g}s" if self.timeout is not None else ""
        except (TypeError, ValueError):
            timeout_suffix = f" after {self.timeout}s" if self.timeout is not None else ""
        super().__init__(
            f"Ollama model '{model or 'unknown'}' timed out{timeout_suffix} after {attempts} attempts."
        )


class OllamaConnector:
    """
    Lean sync connector for Ollama.
    - Reuses one HTTP session
    - Tracks context per-bot or shared
    """


    def __init__(self) -> None:
        self.independent_contexts: bool = False
        self.augmenting_prompt: bool = False

        self.temperature: int | float | None = None
        self.top_p: float | None = None
        self.top_k: int | None = None
        self.timeout: float | None = None
        self.max_tokens: int | None = None
        self.stop: list[str] | None = None
        self.seed: int | None = None
        self.num_thread: int | None = None
        self.model: str = ""
        self.num_ctx: int | None = None
        self.num_predict: int | None = None

        self.client = None
        self._client_host: str | None = None
        self._client_timeout: float | str | None = None
        self._system_instructions: str = ""
        self._history_by_bot: dict[int, list[Message]] = {}
        self._history_shared: list[Message] = []

        turns_per_round = config.get("game", "turns_per_round") or 10
        max_hist_cfg = config.get("llm", "max_history_messages")
        self._max_history_messages: int = int(max_hist_cfg or (int(turns_per_round) * 2))

        self.load_options(force=True)


    def _ensure_system_message(self, history) -> None:
        """Ensure the system header (if any) is at messages[0]."""

        # if self._system_instructions is None or empty string
        if self._system_instructions is None or not self._system_instructions.strip():
            # If we don't have system instructions we remove it from the history
            if history and history[0].get("role") == "system":
                del history[0]
            return

        if len(history) == 0:
            history.insert(0, {"role": "system", "content": self._system_instructions})

        elif history[0].get("role") != "system":
            history.insert(0, {"role": "system", "content": self._system_instructions})

        elif history[0].get("content") != self._system_instructions:
            history[0]["content"] = self._system_instructions


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
            game_state_json = json.dumps(
                game_state,
                separators=(",", ":"),
                ensure_ascii=False,
            )
            content = f"[GAME_STATE]\n{game_state_json}\n[PLAYER_INPUT]\n{player_text}"

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
        self._ensure_system_message(history)  # ensure system message is at index 0
        # TODO verify this works OK

    def _remove_message_instance(self, history: List[Message], message: Message) -> None:
        """Remove a specific message object from a history list if it is still present."""
        for index in range(len(history) - 1, -1, -1):
            if history[index] is message:
                del history[index]
                break



    def load_options(self, force: bool = False) -> None:
        """Load configuration and ensure client and contexts are consistent."""
        # TODO create a yaml for default settings

        # Read from config (cast to proper types)
        self.temperature = _maybe_float(config.get("llm", "temperature"))
        self.top_p = _maybe_float(config.get("llm", "top_p"))
        self.top_k = _maybe_int(config.get("llm", "top_k"))

        self.model = str(config.get("llm", "model") or "").strip()
        self.timeout = ollama_service.resolve_request_timeout(
            {
                "model": self.model,
                "model_timeouts": config.get("llm", "model_timeouts"),
                "timeout": config.get("llm", "timeout"),
            },
            model=self.model,
        )

        self.num_thread = _maybe_int(config.get("llm", "num_thread"))
        self.seed = _maybe_int(config.get("llm", "seed"))
        self.stop = _maybe_int(config.get("llm", "stop"))

        self.num_ctx = _maybe_int(config.get("llm", "num_ctx"))
        self.num_predict = _maybe_int(config.get("llm", "num_predict"))

        self.max_tokens = config.get("llm", "max_tokens") or None
        self.stop = config.get("llm", "stop") or None

        url = config.get("llm", "url")
        port = config.get("llm", "port")
        path = config.get("llm", "path")
        self.endpoint = f"{url}:{port}{path}"
        host = f"{url}:{port}"

        self.independent_contexts = config.get("game", "independent_contexts")
        self.augmenting_prompt = config.get("game", "prompt_augmentation")

        # Reset contexts when requested
        if force:
            self.reset_histories()

        # Client setup
        if (
            self.client is None
            or force
            or host != self._client_host
            or self.timeout != self._client_timeout
        ):
            # Use the module-level `Client` symbol so tests can monkeypatch
            # `game.ollama_connector.Client` as the legacy code did.
            self.client = Client(host=host, timeout=self.timeout)
            self._client_host = host
            self._client_timeout = self.timeout



    def process_settings(
        self,
        bot_id: int,
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

        if augmenting_prompt is not None:
            self.augmenting_prompt = augmenting_prompt
            # store change in config without saving it
            config.set("game", "prompt_augmentation", augmenting_prompt)

        if independent_contexts is not None:
            self.independent_contexts = independent_contexts
            # store change in config without saving it
            config.set("game", "independent_contexts", independent_contexts)

        # Histories from a prior mode might be not compatible with the new mode so we allow them to be reset them if the mode changed.
        if reset_histories_on_mode_change and mode_changed:
            self.reset_histories()

        # Reload system instructions
        self._system_instructions = self._get_system_instructions_text()
        self._ensure_system_message(self._get_history_ref(bot_id))

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




        self.process_settings(bot_id=bot_id,
                              augmenting_prompt=new_augmenting_prompt,
                              independent_contexts=new_independent_contexts,
                              reset_histories_on_mode_change=True
                              )


        if reset:
            self.reset_histories()

        self.load_options()


        history = self._get_history_ref(bot_id)
        user_message = self._build_user_message(game_state=game_state, player_text=user_text)
        history.append(user_message)
        self._ensure_system_message(history)
        self._trim_history_inplace(history)

        options = self.gen_options()
        res: "ChatResponse" | dict[str, Any]
        last_timeout: BaseException | None = None

        for attempt in range(1, 3):
            try:
                res = self.client.chat(
                    model=self.model,
                    messages=history,
                    options=options,
                    stream=False,
                )
                break
            except TIMEOUT_EXCEPTIONS as exc:
                last_timeout = exc
                if attempt == 2:
                    self._remove_message_instance(history, user_message)
                    raise LLMTimeoutError(
                        model=self.model,
                        timeout=self.timeout,
                        attempts=attempt,
                        original_exception=exc,
                    ) from exc
        else:  # pragma: no cover - loop always exits via break/raise
            raise AssertionError("Unreachable Ollama retry state.")

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

        last_served_model = str(config.get("llm", "last_served_model") or "").strip()
        if self.model and self.model != last_served_model:
            config.set("llm", "last_served_model", self.model)
            config.save()

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
            if self.independent_contexts:
                key = "system_instructions_not_augmented_independent"
            else:
                key = "system_instructions_not_augmented_shared"
        else:
            if self.independent_contexts:
                key = "system_instructions_augmented_independent"
            else:
                key = "system_instructions_augmented_shared"


        # Get the path to the augmentation header text file from the config
        filename = config.get("llm", key)
        path = resolve_repo_relative(filename)

        try:
            with path.open("r", encoding="utf-8") as f:
                inst = f.read()
                return inst

        except FileNotFoundError as exc:
            raise FileNotFoundError(f"System instructions file not found: {path}") from exc
