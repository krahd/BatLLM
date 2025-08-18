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

import json
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from configs.app_config import config



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

        base: str = str(config.get("llm", "url"))
        port: str = str(config.get("llm", "port"))
        path: str = str(config.get("llm", "path"))

        self.endpoint: str = f"{base}:{port}{path}"
        self.history: List[Dict[str, str]] = []




    def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        req = Request(self.endpoint, data=data, headers={
            "Content-Type": "application/json"}, method="POST")

        try:
            with urlopen(req, timeout=60) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else {}

        except HTTPError as e:
            try:
                body_bytes = e.read()
                body = body_bytes.decode("utf-8", errors="replace")
            except (OSError, AttributeError):
                body = str(e)
            return {"error": f"HTTP {e.code}", "details": body}

        except URLError as e:
            return {"error": "Network error", "details": str(e)}



    def _ensure_system_message(self, text: Optional[str]) -> None:
        if text is None:
            return

        if self.history and self.history[0].get("role") == "system":
            self.history[0]["content"] = text

        else:
            self.history.insert(0, {"role": "system", "content": text})


    def _build_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"model": self.model,
                                   "messages": self.history, "stream": False}

        if self.num_ctx:
            payload["options"] = {"num_ctx": self.num_ctx}

        return payload


    def send_prompt_to_llm(self, user_input: str) -> Optional[str]:
        """Send a request

        Args:
            user_input (str): the prompt

        Returns:
            Optional[str]: the response
        """
        self.history.append({"role": "user", "content": user_input})
        res = self._post(self._build_payload())

        if "error" in res:
            print(f"[error] {res['error']}: {res.get('details', '')}")
            return None


        # Support common response shapes
        content = ""
        if isinstance(res.get("message"), dict) and isinstance(res["message"].get("content"), str):
            content = res["message"]["content"]

        elif isinstance(res.get("response"), str):
            content = res["response"]

        elif isinstance(res.get("choices"), list) and res["choices"]:
            msg = (res["choices"][0] or {}).get("message") or {}
            content = msg.get("content", "")

        content = (content or "").strip()

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
        print(f"Endpoint: {self.endpoint}")
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
