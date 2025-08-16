"""Module responsible for communication with the LLM.
It uses Ollama API to send requests and receive responses and stores the context of the conversation.
"""

import json
from typing import Callable, Any, Dict, List, Optional
from configs.app_config import config
from game.bot import Bot
import asyncio
from ollama import AsyncClient

class OllamaConnector:
    """
    OllamaConnector is a class responsible for managing the connection to the Ollama API.
.
    """
    augmenting_prompt: bool = True
    independent_contexts: bool = False




    def __init__(self) -> None:
        self.augmenting_prompt = None
        self.independent_contexts = None

        self.ctx_by_bot = None
        self.ctx_shared = None

        self.header = None
        self.model = None
        self.num_ctx = None
        self.endpoint: None
        self.temperature = None
        self.timeout = None
        self.top_p = None
        self.top_k = None
        self.max_tokens = None
        self.stop = None
        self.seed = None
        self.num_thread = None
        self.model = None
        self.endpoint: None
        self.num_ctx = None
        self.num_predict = None

        self.client = None



    def _build_payload(self, bot_id: int, user_text: str, seed=False):
        """
        Builds the payload for the Ollama API request based on the bot's context and configuration.

        Args:
            bot (Bot): The bot instance for which the payload is being built.
            seed (bool): If True, the payload is built for seeding the context (the llm forgets the previous context).

        Returns:
            The payload to be sent to the Ollama API.
        """

        payload = {"model": self.model, "stream": False}

        # if seed or there is no context, we create a new context and add the system message with self.header
        if seed or self.ctx_by_bot[bot_id] is None if self.independent_contexts else self.ctx_shared is None:
            messages = []

            if self.header is not None and self.header != "":
                messages.append({"role": "system", "content": self.header})

            messages.append({"role": "user", "content": user_text})

        else:
            messages = [{"role": "user", "content": bot.get_current_prompt()}]
            # we don't return the context because it's stored in self.ctx_by_bot or self.ctx_shared
            # and can be accessed with self._current_ctx(bot_id)

        return payload


    def load_options(self, bot_id: int, force=False) -> None:
        """
        Loads the configuration options from the app_config.
        Creates the Client instance if it does not exist or if force is True.
        Updates the options exposed by the game interface from the UI and the rest from the config
        NOTE: When a new option is exposed by the UI 
        we **must** move it from load_options to update_options_exposed_by_ui

        Args:
            force (bool): If True, creates a new Client instance even if it already exists.
        """

        self.temperature = Optional[int] = config.get("llm", "temperature")
        self.top_p = Optional[int] = config.get("llm", "top_p")
        self.top_k = Optional[int] = config.get("llm", "top_k")
        self.timeout = config.get("llm", "timeout")
        self.max_tokens: Optional[int] = config.get("llm", "max_tokens") or None

        self.stop = Optional[int] = config.get("llm", "stop") or None
        self.seed = Optional[int] = config.get("llm", "seed") or None
        self.num_thread = Optional[int] = config.get("llm", "num_thread") or None

        self.model = config.get("llm", "model")
        self.endpoint: str = f"{config.get("llm", "url")}:{config.get("llm", "port")}{config.get("llm", "path")}"
        self.num_ctx = config.get("llm", "num_ctx") or None
        self.num_predict: Optional[int] = config.get("llm", "num_predict") or None

        self.header = self._get_mode_header_text()


        if self.ctx_by_bot is None or force:
            self.ctx_by_bot: Dict[int, Optional[List[int]]] = {bot.id: None for bot in bot.board_widget.bots}

        if self.ctx_shared is None or force:
            self.ctx_shared = Optional[List[int]] = None

        self.ctx_by_bot: Dict[int, Optional[List[int]]] = {}
        self.ctx_shared: Optional[List[int]] = None

        if self.client is None or force:
            self.client = Client(host=host, timeout=self.timeout)



    def update_options_exposed_by_ui(self, augmenting_prompt, independent_contexts) -> None:
        self.augmenting_prompt = augmenting_prompt
        self.independent_contexts = independent_contexts



    def gen_options(self, bot_id: int, : Bot, force=False) -> dict:
        """
        Refreshes all the connector's options and returns the generation options for the Ollama API request.
        Returns the generation options for the Ollama API request.

        Returns:
            dict: A dictionary containing the generation options.
        """

        self.load_options(bot, force)  # Load or refresh the options from the config and the UI
        res = {}

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

        if self.header is not None and self.header != "":
            res["header"] = self.header

        if self.num_ctx is not None:
            res["num_ctx"] = self.num_ctx

        return res



    def send_prompt_to_llm_sync(self,
                                bot_id: int,
                                *,
                                ctx: Optional[List[int]],
                                user_text: str,
                                new_augmenting_prompt: bool = None,
                                new_independent_contexts: bool = None,

                                ) -> str:

        """
        Sends a syc request to the Ollama API 

        Args:
            bot_id (int): The ID of the bot for which the request is being sent.
            ctx (Optional[List[int]]): The context to be used for the request.
            user_text (str): The user input text to be sent to the LLM.
            new_augmenting_prompt (bool, optional): If provided, overrides the current augmenting prompt setting.
            new_independent_contexts (bool, optional): If provided, overrides the current independent contexts setting.
        """

        if new_augmenting_prompt is not None:
            self.augmenting_prompt = new_augmenting_prompt

        if new_independent_contexts is not None:
            self.independent_contexts = new_independent_contexts


        # Users can change the mode of the game without restarting or saving the preferences
        # therefore we need to check the mode every time we send a request
        self.load_options(bot_id)

        payload = self._build_payload(bot, self.gen_options(bot))

        client = Client(host=self.endpoint, header={"Content-Type": "application/json"})
        response = client.chat(payload)  # TODO change this to a new client method

        if response.error:
            raise Exception(f"Error from Ollama: {response.error}")


        # Store the context for the bot
        if self.independent_contexts:
            self.ctx_by_bot[bot.id] = response.context
        else:
            self.ctx_shared = response.context

        # Let the bot handle the response
        bot._on_llm_response(response.message.content)



        # -- context management helpers: reset, _current_ctx, _store_ctx --
        def reset_contexts(self) -> None:
            self.ctx_by_bot.clear()
            self.shared_ctx = None

        def _current_ctx(self, bot_id: int) -> Optional[List[int]]:
            return self.ctx_by_bot.get(bot_id) if self.independent_contexts else self.shared_ctx

        def _store_ctx(self, bot_id: int, ctx: Optional[List[int]]) -> None:
            if ctx is None:
                return

            if self.independent_contexts:
                self.ctx_by_bot[bot_id] = ctx

            else:
                self.shared_ctx = ctx



        def _get_mode_header_text(self) -> str:
            """Loads from assets/headers the header (system prompt) text for the LLM request based on the mode.

        Returns:
            str: _description_
        """

            # Determine the key based on the mode and context type (2x2 matrix)
            if not self.augmenting_prompt:
            key = ("not_augmented_header_independent" if self.independent_contexts else "not_augmented_header_shared")

            else:
            key = ("augmented_header_independent" if self.independent_contexts else "augmented_header_shared")

            # Get the path to the augmentation header text file from the config
            path = config.get("llm", key)

            try:
            with open(path, "r", encoding="utf-8") as f:
            return f.read()

            except FileNotFoundError:
            raise FileNotFoundError(f"Augmentation header file not found: {path}")
