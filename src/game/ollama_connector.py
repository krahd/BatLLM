"""Ollama connector: manages chat requests and per-bot/shared contexts."""
from typing import Any, Dict, List, Optional

from ollama import Client

from configs.app_config import config


class OllamaConnector:
    """Manages the connection to the Ollama API and tracks chat contexts."""

    def __init__(self) -> None:
        # HTTP client
        self.client: Optional[Client] = None

        # Contexts
        self.ctx_by_bot: Dict[int, Optional[List[int]]] = {}
        self.ctx_shared: Optional[List[int]] = None
        self.independent_contexts: bool = False
        self.augmenting_prompt: bool = False

        # LLM options (defaults)
        self.temperature: Optional[float] = None
        self.top_p: Optional[float] = None
        self.top_k: Optional[int] = None
        self.timeout: Optional[float] = None
        self.max_tokens: Optional[int] = None
        self.stop: Optional[Any] = None
        self.seed: Optional[int] = None
        self.num_thread: Optional[int] = None
        self.model: str = ""
        self.endpoint: str = ""
        self.num_ctx: Optional[int] = None
        self.num_predict: Optional[int] = None
        self.system_instructions: str = ""



    def load_options(self, force: bool = False) -> None:
        """Load configuration and ensure client and contexts are consistent."""

        # Read from config
        self.temperature = config.get("llm", "temperature")
        self.top_p = config.get("llm", "top_p")
        self.top_k = config.get("llm", "top_k")
        self.timeout = config.get("llm", "timeout")
        self.max_tokens = config.get("llm", "max_tokens") or None
        self.stop = config.get("llm", "stop") or None
        self.seed = config.get("llm", "seed") or None
        self.num_thread = config.get("llm", "num_thread") or None

        self.model = config.get("llm", "model")
        url = config.get("llm", "url")
        port = config.get("llm", "port")
        path = config.get("llm", "path")
        self.endpoint = f"{url}:{port}{path}"
        host = f"{url}:{port}"
        self.num_ctx = config.get("llm", "num_ctx") or None
        self.num_predict = config.get("llm", "num_predict") or None

        self.system_instructions = self._get_system_instructions_text()

        # Reset contexts when requested
        if force:
            self.ctx_by_bot: Dict[int, Optional[List[int]]] = {}
            self.ctx_shared: Optional[List[int]] = None

        # Client setup
        if self.client is None or force:
            self.client = Client(host=host, timeout=self.timeout)



    def update_options_exposed_by_ui(self, *, augmenting_prompt: bool, independent_contexts: bool) -> None:
        """updates options exposed by the UI, passed as parameters

        Args:
            augmenting_prompt (bool): _description_
            independent_contexts (bool): _description_
        """
        self.augmenting_prompt = augmenting_prompt
        self.independent_contexts = independent_contexts




    def gen_options(self, bot_id: int, force: bool = False) -> Dict[str, Any]:
        """Refresh connector options and return generation options for chat."""
        # Load or refresh the options from the config and the UI
        self.load_options(force)

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

        if self.system_instructions is not None and self.system_instructions != "":
            res["augmenting_header"] = self.system_instructions

        if self.num_ctx is not None:
            res["num_ctx"] = self.num_ctx

        if self.num_predict is not None:
            res["num_predict"] = self.num_predict

        return res


    # the * in a function signature makes everything after it keyword-only (PEP 3102).
    # so here all the arguments must be passed by name 'cept for bot_id.
    def send_prompt_to_llm_sync(
        self,
        bot_id: int,
        *,
        user_text: str,
        new_augmenting_prompt: Optional[bool] = None,
        new_independent_contexts: Optional[bool] = None,

    ) -> str:
        """
        Send a synchronous chat request to the Ollama API.
        """
        if new_augmenting_prompt is not None:
            self.augmenting_prompt = new_augmenting_prompt

        if new_independent_contexts is not None:
            self.independent_contexts = new_independent_contexts

        self.load_options(bot_id)
        ctx = self._current_ctx(bot_id)

        if self.seed or ctx is None:
            # If seed set or no context, start a new context and include augmenting_header
            messages = []

            if self.system_instructions is not None and self.system_instructions != "":
                messages.append({"role": "system", "content": self.system_instructions})

            messages.append({"role": "user", "content": user_text})
            res = self.client.chat(model=self.model,
                                   messages=messages,
                                   options=self.gen_options(bot_id),
                                   stream=False,
                                   )
        else:
            messages = [{"role": "user", "content": user_text}]
            res = self.client.chat(
                model=self.model,
                messages=messages,
                options=self.gen_options(bot_id),
                stream=False,
            )

        # Expected shape: {'message': {'role': 'assistant', 'content': '...'}, 'context': [...]}
        if not isinstance(res, dict):
            raise RuntimeError(f"Unexpected response type: {type(res)}")

        # Save updated context
        self._store_ctx(bot_id, res.get("context"))

        # Extract content
        content = ""
        if isinstance(res.get("message"), dict):
            content = (res["message"].get("content") or "").strip()
        elif isinstance(res.get("response"), str):
            content = res["response"].strip()

        if not content:
            raise RuntimeError(f"Empty content from model: {res}")

        return content

    # -- context management helpers: reset, _current_ctx, _store_ctx --
    def reset_contexts(self) -> None:
        """new ctxds
        """
        self.ctx_by_bot.clear()
        self.ctx_shared = None


    def _current_ctx(self, bot_id: int) -> Optional[List[int]]:
        return self.ctx_by_bot.get(bot_id) if self.independent_contexts else self.ctx_shared


    def _store_ctx(self, bot_id: int, ctx: Optional[List[int]]) -> None:
        if ctx is None:
            return
        if self.independent_contexts:
            self.ctx_by_bot[bot_id] = ctx
        else:
            self.ctx_shared = ctx



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
