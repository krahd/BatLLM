from game.bot import Bot
from configs.app_config import config
import sys
import os
from pathlib import Path
from types import SimpleNamespace

# Ensure 'src' (this file's parent) is on sys.path for local imports
SRC_DIR = Path(__file__).resolve().parents[1]  # .../BatLLM/src
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


class DummyHistory:
    """
    DummyHistory is a simple class for simulating and recording chat history in a game-like structure.

    Attributes:
        current_game (dict): Stores the overall game state, including all rounds.
        current_round (dict): Represents the current round, containing its turns.
        current_turn (dict): Represents the current turn, containing its messages.

    Methods:
        record_message(bot_id, role, content):
            Records a message in the current turn with the specified bot ID, role, and content.

        get_chat_history(bot_id=None, shared=True):
            Retrieves the chat history for the current turn.
            If 'shared' is True or 'bot_id' is None, returns all messages.
            Otherwise, returns only messages sent by the specified bot ID.
    """

    def __init__(self):
        self.current_game = {"rounds": []}
        self.current_round = {"round": 1, "turns": []}
        self.current_game["rounds"].append(self.current_round)
        self.current_turn = {"turn": 1, "messages": []}
        self.current_round["turns"].append(self.current_turn)

    def record_message(self, bot_id, role, content):
        """
        Records a message in the current conversation turn.

        Args:
            bot_id (str): Identifier of the bot sending or receiving the message.
            role (str): The role of the message sender (e.g., 'user', 'assistant').
            content (str): The content of the message.

        Side Effects:
            Appends a dictionary representing the message to the 'messages' list in the current turn.
            Initializes the 'messages' list if it does not exist.
        """
        self.current_turn.setdefault("messages", []).append(
            {"bot_id": bot_id, "role": role, "content": content}
        )

    def get_chat_history(self, bot_id=None, shared=True):
        """
        Retrieve the chat history for the current turn, optionally filtered by bot ID and sharing status.

        Args:
            bot_id (Optional[Any]): The identifier of the bot whose messages should be included. If None, includes all bots.
            shared (bool): If True, includes all messages regardless of bot ID. If False, filters messages by the specified bot_id.

        Returns:
            List[Dict[str, str]]: A list of message dictionaries, each containing 'role' and 'content' keys.
        """
        out = []
        for msg in self.current_turn.get("messages", []):
            if shared or bot_id is None or msg["bot_id"] == bot_id:
                out.append({"role": msg["role"], "content": msg["content"]})
        return out


class DummyBoard:
    """
    DummyBoard is a mock class simulating a board interface for testing LLM interactions.

    Attributes:
        history_manager (DummyHistory): Manages the history of interactions.
        ollama_connector (SimpleNamespace): Simulates sending requests to an LLM backend.
        bots (list): List of bot instances associated with the board.

    Methods:
        on_bot_llm_interaction_complete(bot):
            Callback invoked when a bot's LLM interaction is complete.

        add_llm_response_to_history(bot_id, cmd):
            Logs the LLM response command for a given bot.

        add_text_to_llm_response_history(bot_id, text):
            Logs additional text to the LLM response history for a given bot.

        get_bot_by_id(bot_id):
            Retrieves a bot instance by its ID.

        shoot(bot_id):
            Simulates a shoot action by a bot.
    """

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
