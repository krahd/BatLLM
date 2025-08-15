"""
conversation_cli.py
====================

This module provides a minimal interactive command-line chat client for the BatLLM model,
configured via `config.yaml`. It enables users to interact with an Ollama-compatible LLM
endpoint, maintaining conversation history for context and supporting basic commands.

Classes:
    ConversationCLI: 
        - Handles user interaction, message history, and communication with the LLM API.
        - Supports commands:
            /exit  -> quit the chat session
            /reset -> clear conversation history
            /sys <text> -> set or replace the system prompt
            /history -> display current conversation history

Usage:
    Run this script directly to start an interactive chat session with the configured model.
    The client prints the endpoint and available commands, and gracefully handles exit signals.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from configs.app_config import config




class ConversationCLI:
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
        self.model: str = str(config.get("llm", "model") or "llama3.2:latest")
        self.num_ctx: int = int(config.get("llm", "num_ctx") or 0)

        base: str = str(config.get("llm", "url") or "http://localhost").rstrip("/")
        port: str = str(config.get("llm", "port") or "11434")
        path: str = str(config.get("llm", "path") or "/api/chat")

        self.endpoint: str = f"{base}:{port}{path}"
        self.messages: List[Dict[str, str]] = []



    # ---------------- HTTP ----------------
    def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        req = Request(self.endpoint, data=data, headers={"Content-Type": "application/json"}, method="POST")

        try:
            with urlopen(req, timeout=60) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else {}

        except HTTPError as e:
            try:
                body = e.read().decode("utf-8")
                return {"error": f"HTTP {e.code}", "details": body}

            except Exception:
                return {"error": f"HTTP {e.code}", "details": str(e)}

        except URLError as e:
            return {"error": "Network error", "details": str(e)}


    # -------------- Chat core --------------
    def _ensure_system(self, text: Optional[str]) -> None:
        if text is None:
            return

        if self.messages and self.messages[0].get("role") == "system":
            self.messages[0]["content"] = text
        else:
            self.messages.insert(0, {"role": "system", "content": text})


    def _build_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"model": self.model, "messages": self.messages, "stream": False}

        if self.num_ctx:
            payload["options"] = {"num_ctx": self.num_ctx}
        return payload


    def chat_once(self, user_input: str) -> Optional[str]:
        self.messages.append({"role": "user", "content": user_input})
        res = self._post(self._build_payload())

        if "error" in res:
            print(f"[error] {res['error']}: {res.get('details', '')}")
            return None


        # Support common response shapes
        content = ""
        if isinstance(res.get("message"), dict) and isinstance(res["message"].get("content"), str):
            content = res["message"]["content"]
            print("h1")

        elif isinstance(res.get("response"), str):
            content = res["response"]
            print("h2")

        elif isinstance(res.get("choices"), list) and res["choices"]:
            msg = (res["choices"][0] or {}).get("message") or {}
            content = msg.get("content", "")
            print("h3")

        content = (content or "").strip()

        if content:
            self.messages.append({"role": "assistant", "content": content})
            return content

        else:
            print("[warn] Empty response from model")
            return None



    def run(self) -> None:
        """
        Starts an interactive command-line chat session with the BatLLM model.

        Displays the current endpoint and available commands to the user. 
        Supports the following commands:
            - /exit: Exit the chat session.
            - /reset: Clear the conversation history.
            - /sys <text>: Set the system prompt to <text>.
            - /history: Display the current conversation history.

        For each user input, sends the message to the model and prints the response.
        Handles EOF and keyboard interrupts gracefully by exiting the session.
        """
        print("Interactive chat with BatLLM model.")
        print(f"Endpoint: {self.endpoint}")
        print("Commands: /exit, /reset, /sys <text>\n")

        while True:
            try:
                line = input("you> ").strip()

            except (EOFError, KeyboardInterrupt):
                print()  # newline
                break

            if not line:
                continue

            if line == "/exit":
                break

            if line == "/reset":
                self.messages.clear()
                print("[ok] History cleared")
                continue

            if line.startswith("/sys "):
                self._ensure_system(line[5:].strip())
                print("[ok] System prompt set")

            if line == "/history":
                print("[ok] Current conversation history:")
                for msg in self.messages:
                    print(f"{msg['role']}: {msg['content']}")
                continue

            reply = self.chat_once(line)
            if reply is not None:
                print(f"bot> {reply}\n")


if __name__ == "__main__":
    ConversationCLI().run()
