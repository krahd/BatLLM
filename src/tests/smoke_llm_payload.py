import sys
import os
from pathlib import Path
from types import SimpleNamespace

# Ensure 'src' (this file's parent) is on sys.path for local imports
SRC_DIR = Path(__file__).resolve().parents[1]  # .../BatLLM/src
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from configs.app_config import config
from game.bot import Bot


class DummyHistory:
    def __init__(self):
        self.current_game = {"rounds": []}
        self.current_round = {"round": 1, "turns": []}
        self.current_game["rounds"].append(self.current_round)
        self.current_turn = {"turn": 1, "messages": []}
        self.current_round["turns"].append(self.current_turn)

    def record_message(self, bot_id, role, content):
        self.current_turn.setdefault("messages", []).append(
            {"bot_id": bot_id, "role": role, "content": content}
        )

    def get_chat_history(self, bot_id=None, shared=True):
        out = []
        for msg in self.current_turn.get("messages", []):
            if shared or bot_id is None or msg["bot_id"] == bot_id:
                out.append({"role": msg["role"], "content": msg["content"]})
        return out


class DummyBoard:
    def __init__(self):
        self.history_manager = DummyHistory()
        self.ollama_connector = SimpleNamespace(
            send_request=lambda url, data, on_success, on_failure, on_error: on_success(
                None, {"response": "M"}
            )
        )
        self.bots = []

    def on_bot_llm_interaction_complete(self, bot):
        pass

    def add_llm_response_to_history(self, bot_id, cmd):
        print(f"UI log: bot {bot_id} -> {cmd}")

    def add_text_to_llm_response_history(self, bot_id, text):
        print(f"UI note: {text.strip()}")

    def get_bot_by_id(self, bot_id):
        for b in self.bots:
            if b.id == bot_id:
                return b
        return None

    def shoot(self, bot_id):
        print(f"Shoot by {bot_id}")


if __name__ == "__main__":
    # Force debug printing
    config.set("llm", "debug_requests", True)

    board = DummyBoard()

    b1 = Bot(1, board)
    b2 = Bot(2, board)
    board.bots = [b1, b2]

    b1.prepare_prompt_submission("Move forward")
    b2.prepare_prompt_submission("Rotate right 10")

    # Call the submit to build messages and trigger dummy response
    b1.submit_prompt_to_llm()
    b2.submit_prompt_to_llm()

    # Show recorded history
    hist = board.history_manager.get_chat_history(shared=True)
    print("History size:", len(hist))
    for i, m in enumerate(hist, 1):
        print(i, m["role"], m["content"].splitlines()[0])
