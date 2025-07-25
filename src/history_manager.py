import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict
from datetime import datetime

@dataclass
class TurnRecord:
    turn_number: int
    order: int
    llm_response: str
    pre_state: Dict[str, float]
    post_state: Dict[str, float]

@dataclass
class RoundRecord:
    round_number: int
    prompts: List[str]  # [prompt_bot1, prompt_bot2]
    augmented: bool
    independent_llms: bool
    turns: List[TurnRecord] = field(default_factory=list)

@dataclass
class GameRecord:
    game_number: int
    turns_per_round: int
    rounds: List[RoundRecord] = field(default_factory=list)
    total_rounds: int = 0

class HistoryManager:
    def __init__(self):
        self.session_start = datetime.now().isoformat()
        self.session_end = None
        self.games: List[GameRecord] = []
        self._current_game: GameRecord = None
        self._current_round: RoundRecord = None
        self._current_game_config = {}

    def start_new_game(self, augmented: bool, independent_llms: bool):
        game_num = len(self.games) + 1
        game = GameRecord(game_number=game_num, turns_per_round=2)
        self.games.append(game)
        self._current_game = game
        self._current_game_config = {
            "augmented": augmented,
            "independent_llms": independent_llms
        }

    def start_new_round(self, prompt_bot1: str, prompt_bot2: str):
        if self._current_game is None:
            raise RuntimeError("No active game to start a round in.")
        round_num = len(self._current_game.rounds) + 1
        new_round = RoundRecord(
            round_number=round_num,
            prompts=[prompt_bot1, prompt_bot2],
            augmented=self._current_game_config["augmented"],
            independent_llms=self._current_game_config["independent_llms"]
        )
        self._current_game.rounds.append(new_round)
        self._current_round = new_round

    def record_turn(self, order: int, llm_response: str, pre_state: Dict[str, float], post_state: Dict[str, float]):
        if self._current_round is None:
            raise RuntimeError("No active round to record a turn in.")
        turn_num = len(self._current_round.turns) + 1
        turn_entry = TurnRecord(
            turn_number=turn_num,
            order=order,
            llm_response=llm_response,
            pre_state=pre_state.copy(),
            post_state=post_state.copy()
        )
        self._current_round.turns.append(turn_entry)

    def end_current_game(self):
        if self._current_game:
            self._current_game.total_rounds = len(self._current_game.rounds)
            self._current_game = None
            self._current_round = None
            self._current_game_config = {}

    def save_session(self, filepath: str):
        self.session_end = datetime.now().isoformat()
        session_data = {
            "session_start": self.session_start,
            "session_end": self.session_end,
            "games": [asdict(game) for game in self.games]
        }
        with open(filepath, 'w') as f:
            json.dump(session_data, f, indent=4)

    def clear_history(self):
        self.__init__()