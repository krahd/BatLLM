"""Module responsible for communication with the LLM.
It uses Ollama API to send requests and receive responses and stores the context of the conversation.
"""

import json
from typing import Callable, Any
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
        self.augmenting_prompt: bool = True
        self.independent_contexts: bool = False
        self.ctx_by_bot = {1: None, 2: None}
        self.ctx = None
        self.header = None
        self.model = config.get("llm", "model")
        self.num_ctx = config.get("llm", "num_ctx")

        base = config.get("llm", "url")
        port = config.get("llm", "port")
        path = config.get("llm", "path")

        self.endpoint: str = f"{base}:{port}{path}"


    def _build_payload(self, bot: Bot, seed=False):
        """
        Builds the payload for the Ollama API request based on the bot's context and configuration.

        Args:
            bot (Bot): The bot instance for which the payload is being built.
            seed (bool): If True, the payload is built for seeding the context (the llm forgets the previous context).

        Returns:
            The payload to be sent to the Ollama API.
        """

        payload = {"model": self.model, "stream": False}
        # if seed or no context
        if seed or self.ctx_by_bot[bot.id] is None if self.independent_contexts else self.ctx is None:
            payload["messages"] = [
                {"role": "system", "content": self.header},
                {"role": "user", "content": bot.get_current_prompt()},
            ]

        else:
            payload["messages"] = [{"role": "user", "content": bot.get_current_prompt()}]
            payload["context"] = self.ctx_by_bot[bot.id] if self.independent_contexts else self.ctx

        return payload



    async def send_prompt_to_llm(self, bot: Bot) -> None:
        """
        Sends a request to the Ollama API for the given bot.

        Args:
            bot (Bot): The bot instance for which the request is being sent.
        """

        # Users can change the mode of the game without restarting or saving the preferences
        # therefore we need to check the mode every time we send a request

        self.augmenting_prompt = bot.board_widget.history_manager.augmenting_prompt
        self.independent_contexts = bot.board_widget.history_manager.independent_contexts
        self.header = self._get_mode_header_text()

        payload = self._build_payload(bot)
        # response = await AsyncClient().chat(payload)
        async with AsyncClient() as client:
            response = await client.chat(payload)

        if response.error:
            raise Exception(f"Error from Ollama: {response.error}")


        # Store the context for the bot
        if self.independent_contexts:
            self.ctx_by_bot[bot.id] = response.context
        else:
            self.ctx = response.context

        # Store the last response in the bot
        bot.last_llm_response = response.message.content


        # Store the last command in the bot
        bot.last_cmd = response.message.content.strip() if response.message.content else ""

        # Record the response in the bot's history
        bot.board_widget.history_manager.record_message(
            bot.id, "assistant", bot.last_llm_response
        )
        # Record the play in the bot's history
        bot.board_widget.history_manager.record_play(
            bot.id,
            llm_raw_response=bot.last_llm_response,
            cmd=bot.last_cmd if bot.last_cmd else "ERR",
        )
        # Notify the board that the bot is ready for the next turn
        bot.ready_for_next_turn = True
        bot.board_widget.on_bot_llm_interaction_complete(bot)
        # Notify the bot that the LLM interaction is complete
        bot.on_llm_interaction_complete()
        # Notify the bot that the LLM interaction is complete








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
