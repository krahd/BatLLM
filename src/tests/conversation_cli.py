"""
conversation_cli.py
====================

This module provides a minimal interactive command-line chat client for the BatLLM model,
configured via `config.yaml`. It enables users to interact with an Ollama-compatible LLM
endpoint, maintaining conversation history for context and supporting basic commands.

Classes:
    ConversationCLI:
        - Simple conversation with the LLM.
        - Commands_
            /exit  -> quit
            /reset -> clear history
            /sys [<text>] -> print, set, or replace the system prompt
            /history -> display current history

    set_history(history: List[Dict[str, str]]) -> None:
        - Set the conversation history to a new list of messages. This wwould allow players to
        chat with the model at any point of the game.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from configs.app_config import config
from llm import service as ollama_service
from modelito import Message, OllamaProvider



class ConversationCLI():

    """
      Minimal interactive chat client for the configured Ollama model.

      - Uses llm.url, llm.port, llm.path, llm.model, and llm.num_ctx from config.yaml
      - Maintains message history so the chat has context
      - Commands:
          /exit  -> quit
          /reset -> clear history
          /sys <text> -> set/replace a system prompt as the first message
          /history -> display current conversation history
      """


    def __init__(self) -> None:
        self.model: str = str(config.get("llm", "model"))
        self.num_ctx: int = int(config.get("llm", "num_ctx"))

        self.base_url: str = str(config.get("llm", "url")).rstrip("/")
        self.port: int = int(config.get("llm", "port"))
        self.timeout: float = ollama_service.resolve_request_timeout(
            {
                "model": self.model,
                "model_timeouts": config.get("llm", "model_timeouts") or {},
                "timeout": config.get("llm", "timeout"),
            },
            model=self.model,
        )
        self.provider = OllamaProvider(
            host=self.base_url,
            port=self.port,
            model=self.model,
        )
        self.history: List[Dict[str, str]] = []



    def _ensure_system_message(self, text: Optional[str]) -> None:
        if text is None:
            return

        if self.history and self.history[0].get("role") == "system":
            self.history[0]["content"] = text

        else:
            self.history.insert(0, {"role": "system", "content": text})
    def send_prompt_to_llm(self, user_input: str) -> Optional[str]:
        """Send a request

        Args:
            user_input (str): the prompt

        Returns:
            Optional[str]: the response
        """
        self.history.append({"role": "user", "content": user_input})
        try:
            settings = {"timeout": self.timeout}
            if self.num_ctx:
                settings["num_ctx"] = self.num_ctx
            content = self.provider.summarize(
                [
                    Message(role=msg.get("role", "user"), content=msg.get("content", ""))
                    for msg in self.history
                ],
                settings=settings,
            ).strip()
        except Exception as exc:
            print(f"[error] {exc}")
            return None

        if content:
            self.history.append({"role": "assistant", "content": content})
            return content

        else:
            print("[!!] Empty response from model")
            return None


    def set_history(self, history: List[Dict[str, str]]) -> None:
        """
        Set the conversation history to a new list of messages.

        Args:
            history (List[Dict[str, str]]): List of message dictionaries with 'role' and 'content'.
        """
        self.history = history

    def print_help(self) -> str:
        """Helper for help
        Returns:
            str: a string with the available commands
        """
        print(f"Ollama host: {self.base_url}:{self.port}")
        print("Commands: /exit, /reset, /sys [text], /history, /help, /?\n\n")


    def run(self) -> None:
        """Main loop (chat)
        """

        self.print_help()
        print("")

        while True:
            try:
                line = input("> ").strip()

            except (EOFError, KeyboardInterrupt):
                print()  # newline
                break

            if not line:
                continue

            if line == "/exit":
                break

            if line == "/reset":
                self.history.clear()
                print("[history cleared]")
                continue

            if line.startswith("/sys"):
                sys_msg = line[4:].strip()

                if not (sys_msg is None or sys_msg == ""):
                    sys_msg = sys_msg[0:]
                    self._ensure_system_message(sys_msg)
                    print(f"[system prompt set to: {sys_msg}")

                else:
                    print(f"[history[0]: {self.history[0]}]")

                continue

            if line == "/history":
                print("<history>")
                for msg in self.history:
                    print(f"{msg['role']}: {msg['content']}")
                print("</history>")
                continue

            if line == "/help" or line == "/?":
                self.print_help()
                continue

            reply = self.send_prompt_to_llm(line)

            if reply is not None:
                print("")
                print(f"--: {reply}\n")
                print("\n")
