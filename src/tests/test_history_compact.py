import sys
from pathlib import Path

# Ensure 'src' is on sys.path
SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from game.history_manager import HistoryManager


class DummyBot:
    def __init__(self, bot_id):
        self.id = bot_id
        self.health = 30
        self.x = 0.5
        self.y = 0.5
        self.rot = 0.0
        self.shield = True
        self.last_llm_response = None

    def get_current_prompt(self):
        return ""


class DummyGame:
    def __init__(self):
        self.bots = [DummyBot(1), DummyBot(2)]


if __name__ == "__main__":
    hm = HistoryManager()
    game = DummyGame()

    # Start game and round
    hm.start_game(game)
    hm.start_round(game)

    # Add prompts
    if hm.current_round is not None:
        hm.current_round["prompts"] = [
            {"bot_id": 1, "prompt": "Move forward"},
            {"bot_id": 2, "prompt": "Rotate right 10"},
        ]

    # Start a turn, record messages and end it to capture post_state
    hm.start_turn(game)
    hm.record_message(1, "user", "PLAYER_INPUT:\nMove forward\n")
    hm.record_message(1, "assistant", "M")
    hm.record_message(2, "user", "PLAYER_INPUT:\nRotate right 10\n")
    hm.record_message(2, "assistant", "C10")
    hm.end_turn(game)

    print("--- Compact ---")
    print(hm.to_compact_text())

    print("\n--- Full ---")
    print(hm.to_text())
