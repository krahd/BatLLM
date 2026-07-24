from __future__ import annotations

import json
import math
from concurrent.futures import Future
from pathlib import Path
from types import SimpleNamespace

import pytest

from configs.app_config import config
from game.bot import Bot
from game.bullet import Bullet
from game.game_board import GameBoard
from game.ollama_connector import LLMTimeoutError, OllamaConnector
from game.prompt_store import PromptStore
from game.session_schema import validate_session_payload
from view.home_screen import HomeScreen


class _FakeSound:
    def play(self) -> None:
        return None


class _FakeKeyboard:
    def bind(self, **_kwargs) -> None:
        return None

    def unbind(self, **_kwargs) -> None:
        return None


class _FakePopup:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self._bindings = {}

    def bind(self, **kwargs):
        self._bindings.update(kwargs)

    def open(self) -> None:
        return None

    def dismiss(self) -> None:
        on_dismiss = self._bindings.get("on_dismiss")
        if on_dismiss is not None:
            on_dismiss(self)


class _ImmediateExecutor:
    """Execute submitted work inline while preserving the Future interface."""

    def submit(self, function, *args, **kwargs):
        future = Future()
        try:
            future.set_result(function(*args, **kwargs))
        except BaseException as exc:  # Future must preserve production exception delivery.
            future.set_exception(exc)
        return future


def _instant_move(self, distance=None, duration: float = 0.48, easing: str = "out_quad", on_complete=None):
    step = self.default_step if distance is None else distance
    rad = math.radians(self.rot)
    self.x += math.cos(rad) * step
    self.y += math.sin(rad) * step
    if on_complete:
        on_complete()


def _instant_rotate(self, angle: float, duration: float = 0.24, easing: str = "out_quad", on_complete=None):
    self.rot = (self.rot + angle) % 360
    if on_complete:
        on_complete()


def _complete_scheduled_turn(scheduled_once, *, finalize_round: bool = False) -> None:
    """Run the turn callback and both UI-thread inference completions."""
    for _ in range(3):
        scheduled_once.pop(0)(0)
    if finalize_round:
        scheduled_once.pop(0)(0)


def _build_board(monkeypatch, overrides: dict[tuple[str, str], object] | None = None):
    overrides = overrides or {}
    original_get = config.get
    monkeypatch.setattr(
        config,
        "get",
        lambda section, key: overrides.get((section, key), original_get(section, key)),
    )
    monkeypatch.setattr("game.game_board.SoundLoader.load", lambda *_args, **_kwargs: _FakeSound())
    monkeypatch.setattr("game.game_board.Popup", _FakePopup)
    monkeypatch.setattr("game.game_board.Label", lambda *args, **kwargs: SimpleNamespace())
    monkeypatch.setattr(
        "game.game_board.Window",
        SimpleNamespace(request_keyboard=lambda *_args, **_kwargs: _FakeKeyboard()),
        raising=False,
    )

    scheduled_once = []
    monkeypatch.setattr(
        "game.game_board.Clock.schedule_interval",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "game.game_board.Clock.schedule_once",
        lambda callback, *_args, **_kwargs: scheduled_once.append(callback),
    )
    monkeypatch.setattr("game.game_board.show_fading_alert", lambda *args, **kwargs: None)
    monkeypatch.setattr("game.bot.get_executor", lambda: _ImmediateExecutor())
    monkeypatch.setattr(Bot, "move", _instant_move)
    monkeypatch.setattr(Bot, "rotate", _instant_rotate)

    board = GameBoard()
    history_log = []
    monkeypatch.setattr(
        board,
        "add_text_to_home_screen_cmd_history",
        lambda bot_id, text: history_log.append((bot_id, text)),
    )
    board.start_new_game()
    scheduled_once.clear()
    return board, scheduled_once, history_log


def test_home_screen_submit_prompt_being_edited_adds_prompt_once() -> None:
    screen = HomeScreen()
    prompt_store = PromptStore()
    submitted = []

    board = SimpleNamespace(
        prompt_store=prompt_store,
        submit_prompt_to_bot=lambda bot_id, prompt: (
            prompt_store.add_prompt(bot_id, prompt),
            submitted.append((bot_id, prompt)),
        ),
    )
    screen.ids = {
        "prompt_input_1": SimpleNamespace(text="Reply with exactly M"),
        "prompt_store_viewer_1": SimpleNamespace(text=""),
        "game_board": board,
    }

    screen.submit_prompt_being_edited(1)

    assert prompt_store.get_current_prompt(1) == "Reply with exactly M"
    assert prompt_store._data[1]["prompts"] == ["Reply with exactly M"]
    assert submitted == [(1, "Reply with exactly M")]
    assert screen.ids["prompt_input_1"].text == ""
    assert screen.ids["prompt_store_viewer_1"].text == "Reply with exactly M"


def test_home_screen_preserves_prompt_rejected_during_active_round(monkeypatch) -> None:
    screen = HomeScreen()
    alerts = []
    screen.ids = {
        "prompt_input_1": SimpleNamespace(text="Keep this prompt"),
        "prompt_store_viewer_1": SimpleNamespace(text="Previous prompt"),
        "game_board": SimpleNamespace(
            submit_prompt_to_bot=lambda _bot_id, _prompt: False
        ),
    }
    monkeypatch.setattr(
        "view.home_screen.show_fading_alert",
        lambda title, message, **_kwargs: alerts.append((title, message)),
    )

    assert screen.submit_prompt_being_edited(1) is False
    assert screen.ids["prompt_input_1"].text == "Keep this prompt"
    assert screen.ids["prompt_store_viewer_1"].text == "Previous prompt"
    assert alerts[0][0] == "Round in progress"


def test_ollama_connector_ensure_system_message_inserts_header_once(monkeypatch) -> None:
    monkeypatch.setattr("game.ollama_connector.Client", lambda *args, **kwargs: object())
    connector = OllamaConnector()
    connector._system_instructions = "SYSTEM HEADER"

    history = [{"role": "user", "content": "move"}]
    connector._ensure_system_message(history)
    connector._ensure_system_message(history)

    assert history[0] == {"role": "system", "content": "SYSTEM HEADER"}
    assert history[1] == {"role": "user", "content": "move"}
    assert [msg["role"] for msg in history].count("system") == 1


def test_ollama_connector_retries_once_after_timeout(monkeypatch) -> None:
    calls = {"count": 0}

    def fake_chat(**_kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise TimeoutError("slow model")
        return SimpleNamespace(message=SimpleNamespace(content="M"))

    monkeypatch.setattr(
        "game.ollama_connector.Client",
        lambda *args, **kwargs: SimpleNamespace(chat=fake_chat),
    )

    connector = OllamaConnector()

    response = connector.send_prompt_to_llm_sync(
        1,
        user_text="Reply with exactly M",
        game_state={},
    )

    assert response == "M"
    assert calls["count"] == 2
    history = connector._get_history_ref(1)
    assert [message["role"] for message in history].count("user") == 1
    assert history[-1] == {"role": "assistant", "content": "M"}


def test_ollama_connector_timeout_raises_typed_error_and_rolls_back_prompt(monkeypatch) -> None:
    monkeypatch.setattr(
        "game.ollama_connector.Client",
        lambda *args, **kwargs: SimpleNamespace(chat=lambda **
                                                _kwargs: (_ for _ in ()).throw(TimeoutError("slow model"))),
    )

    connector = OllamaConnector()

    with pytest.raises(LLMTimeoutError) as exc_info:
        connector.send_prompt_to_llm_sync(
            1,
            user_text="Reply with exactly M",
            game_state={},
        )

    assert exc_info.value.attempts == 2
    history = connector._get_history_ref(1)
    assert all(message["role"] != "user" for message in history)


def test_string_timeout_config_is_normalized_and_timeout_messages_stay_safe(monkeypatch) -> None:
    monkeypatch.setattr(
        "game.ollama_connector.Client",
        lambda *args, **kwargs: SimpleNamespace(),
    )

    board, _scheduled_once, _history_log = _build_board(monkeypatch, overrides={
        ("llm", "timeout"): "120",
    })
    connector = board.ollama_connector

    assert connector.timeout == 120.0
    assert isinstance(connector.timeout, float)

    exc = LLMTimeoutError(
        model="qwen3:30b",
        timeout=connector.timeout,
        attempts=2,
        original_exception=TimeoutError("slow model"),
    )
    assert "120" in str(exc)

    setattr(exc, "timeout", "120")
    message = board._format_timeout_message(board.get_bot_by_id(1), exc)
    assert "after 120s" in message


def test_connector_uses_model_specific_timeout_override(monkeypatch) -> None:
    monkeypatch.setattr(
        "game.ollama_connector.Client",
        lambda *args, **kwargs: SimpleNamespace(
            host=kwargs.get("host"),
            timeout=kwargs.get("timeout"),
        ),
    )

    board, _scheduled_once, _history_log = _build_board(monkeypatch, overrides={
        ("llm", "model"): "qwen3:30b",
        ("llm", "timeout"): 60,
        ("llm", "model_timeouts"): {"qwen3:30b": "180"},
    })

    connector = board.ollama_connector

    assert connector.timeout == 180.0
    assert connector.client.timeout == 180.0


def test_connector_uses_common_model_default_timeout(monkeypatch) -> None:
    monkeypatch.setattr(
        "game.ollama_connector.Client",
        lambda *args, **kwargs: SimpleNamespace(
            host=kwargs.get("host"),
            timeout=kwargs.get("timeout"),
        ),
    )

    board, _scheduled_once, _history_log = _build_board(monkeypatch, overrides={
        ("llm", "model"): "llama3.2:latest",
        ("llm", "timeout"): None,
        ("llm", "model_timeouts"): {},
    })

    connector = board.ollama_connector

    assert connector.timeout == 75.0
    assert connector.client.timeout == 75.0


def test_connector_recreates_client_when_timeout_or_host_changes(monkeypatch) -> None:
    created_clients = []

    def fake_client(*args, **kwargs):
        client = SimpleNamespace(
            host=kwargs.get("host"),
            timeout=kwargs.get("timeout"),
            marker=len(created_clients),
        )
        created_clients.append(client)
        return client

    monkeypatch.setattr("game.ollama_connector.Client", fake_client)

    overrides = {
        ("llm", "timeout"): "120",
    }
    board, _scheduled_once, _history_log = _build_board(monkeypatch, overrides=overrides)
    connector = board.ollama_connector
    initial_client = connector.client

    connector.load_options()
    assert connector.client is initial_client

    overrides[("llm", "timeout")] = "60"
    connector.load_options()

    assert connector.timeout == 60.0
    assert connector.client.timeout == 60.0

    overrides[("llm", "url")] = "http://127.0.0.1"
    connector.load_options()

    assert connector.client.host == "http://127.0.0.1:11434"
    assert len(created_clients) == 3


def test_submit_prompt_to_bot_waits_for_both_players(monkeypatch) -> None:
    board, scheduled_once, _history_log = _build_board(monkeypatch)

    board.submit_prompt_to_bot(1, "M")

    assert board.current_round == 0
    assert scheduled_once == []
    assert board.prompt_store.get_current_prompt(1) == "M"

    board.submit_prompt_to_bot(2, "S1")

    assert board.current_round == 1
    assert len(scheduled_once) == 1
    assert board.history_manager.current_round["prompts"] == [
        {"bot_id": 1, "prompt": "M"},
        {"bot_id": 2, "prompt": "S1"},
    ]


def test_play_turn_records_valid_and_invalid_commands(monkeypatch) -> None:
    board, scheduled_once, history_log = _build_board(monkeypatch, overrides={
        ("game", "turns_per_round"): 2,
    })

    bot_one = board.get_bot_by_id(1)
    bot_two = board.get_bot_by_id(2)
    bot_one.x = 0.2
    bot_one.y = 0.2
    bot_one.rot = 0
    bot_two.x = 0.8
    bot_two.y = 0.8
    bot_two.rot = 180

    responses = {1: "M", 2: "nonsense"}
    monkeypatch.setattr(
        board.ollama_connector,
        "send_prompt_to_llm_sync",
        lambda bot_id, **_kwargs: responses[bot_id],
    )

    board.submit_prompt_to_bot(1, "Reply with exactly M")
    board.submit_prompt_to_bot(2, "Reply with invalid text")
    _complete_scheduled_turn(scheduled_once)

    assert board.current_turn == 1
    plays = board.history_manager.current_round["turns"][0]["plays"]
    by_bot = {play["bot_id"]: play["cmd"] for play in plays}
    assert by_bot == {1: "M", 2: "ERR"}
    assert bot_one.x > 0.2
    assert any("ERR" in text for _bot_id, text in history_log)
    assert len(scheduled_once) == 1


def test_timeout_resolution_can_be_remembered_for_round(monkeypatch) -> None:
    board, _scheduled_once, _history_log = _build_board(monkeypatch)
    bot = board.get_bot_by_id(1)
    timeout_error = LLMTimeoutError(
        model="qwen3:30b",
        timeout=120,
        attempts=2,
        original_exception=TimeoutError("slow model"),
    )
    captured = []

    monkeypatch.setattr(bot, "finish_turn_with_error", lambda raw_response,
                        command="ERR": captured.append((raw_response, command)))

    board._resolve_bot_timeout(bot, timeout_error, action="err", remember_for_round=True)

    assert board._round_timeout_action == "err"
    assert captured and captured[0][1] == "ERR"


def test_play_turn_timeout_can_resolve_as_err(monkeypatch) -> None:
    board, scheduled_once, history_log = _build_board(monkeypatch, overrides={
        ("game", "turns_per_round"): 1,
    })
    monkeypatch.setattr("game.game_board.random.sample", lambda seq, _n: list(seq))

    responses = {
        1: LLMTimeoutError(
            model="qwen3:30b",
            timeout=120,
            attempts=2,
            original_exception=TimeoutError("slow model"),
        ),
        2: "M",
    }

    def fake_send(bot_id, **_kwargs):
        value = responses[bot_id]
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr(board.ollama_connector, "send_prompt_to_llm_sync", fake_send)

    board.submit_prompt_to_bot(1, "Reply slowly")
    board.submit_prompt_to_bot(2, "Reply with exactly M")
    board._round_timeout_action = "err"

    _complete_scheduled_turn(scheduled_once, finalize_round=True)

    round_entry = board.history_manager.games[0]["rounds"][0]
    plays = round_entry["turns"][0]["plays"]
    by_bot = {play["bot_id"]: play["cmd"] for play in plays}

    assert by_bot == {1: "ERR", 2: "M"}
    assert "timed out" in next(play["llm_response"] for play in plays if play["bot_id"] == 1)
    assert board.history_manager.current_round is None
    assert any("Timeout after retry -> ERR" in text for _bot_id, text in history_log)


def test_play_turn_timeout_can_cancel_round_and_roll_back_state(monkeypatch) -> None:
    board, scheduled_once, _history_log = _build_board(monkeypatch, overrides={
        ("game", "turns_per_round"): 2,
        ("game", "total_rounds"): 3,
    })
    monkeypatch.setattr("game.game_board.random.sample", lambda seq, _n: list(seq))

    bot_one = board.get_bot_by_id(1)
    bot_two = board.get_bot_by_id(2)
    bot_one.x, bot_one.y, bot_one.rot = 0.2, 0.2, 0
    bot_two.x, bot_two.y, bot_two.rot = 0.8, 0.8, 180

    responses = {
        1: "M",
        2: LLMTimeoutError(
            model="qwen3:30b",
            timeout=120,
            attempts=2,
            original_exception=TimeoutError("slow model"),
        ),
    }

    def fake_send(bot_id, **_kwargs):
        value = responses[bot_id]
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr(board.ollama_connector, "send_prompt_to_llm_sync", fake_send)

    board.submit_prompt_to_bot(1, "Reply with exactly M")
    board.submit_prompt_to_bot(2, "Reply slowly")
    board._round_timeout_action = "cancel"

    _complete_scheduled_turn(scheduled_once)

    round_entry = board.history_manager.games[0]["rounds"][0]
    cancelled_turn = round_entry["turns"][0]

    assert round_entry["status"] == "cancelled"
    assert round_entry["cancelled_by_bot_id"] == 2
    assert cancelled_turn["status"] == "cancelled"
    assert cancelled_turn["turn"] == 1
    assert cancelled_turn["plays"] == []
    assert cancelled_turn["post_state"] == round_entry["initial_state"]
    assert math.isclose(bot_one.x, 0.2)
    assert math.isclose(bot_one.y, 0.2)
    assert board.current_turn == 0
    assert board.history_manager.current_round is None
    assert scheduled_once == []


def test_shoot_damages_unshielded_target(monkeypatch) -> None:
    board, _scheduled_once, _history_log = _build_board(monkeypatch)

    shooter = board.get_bot_by_id(1)
    target = board.get_bot_by_id(2)
    shooter.x, shooter.y, shooter.rot, shooter.shield = 0.2, 0.5, 0, False
    target.x, target.y, target.shield, target.health = 0.4, 0.5, False, 10

    def _run_until_complete(callback, _interval):
        for _ in range(600):
            keep_running = callback(1 / 60)
            if keep_running is False:
                break
        return None

    monkeypatch.setattr("game.game_board.Clock.schedule_interval", _run_until_complete)

    board.shoot(1)

    assert target.health == 5
    assert board.bullet is None
    assert board.bullet_trace


def test_bot_process_llm_response_supports_canonical_commands(monkeypatch) -> None:
    board, _scheduled_once, _history_log = _build_board(monkeypatch)
    bot = board.get_bot_by_id(1)
    bot.x, bot.y, bot.rot, bot.shield = 0.5, 0.5, 0, False

    completed = []
    shots = []
    monkeypatch.setattr(board, "on_bot_llm_interaction_complete",
                        lambda current_bot: completed.append(current_bot.id))
    monkeypatch.setattr(board, "shoot", lambda bot_id: shots.append(bot_id))

    bot.process_llm_response("M0.3")
    assert math.isclose(bot.x, 0.8)
    assert math.isclose(bot.y, 0.5)
    assert bot.last_cmd == "M0.3"

    bot.ready_for_next_turn = False
    bot.process_llm_response("C90")
    assert bot.rot == 90
    assert bot.last_cmd == "C90.0"

    bot.ready_for_next_turn = False
    bot.process_llm_response("A45")
    assert bot.rot == 45
    assert bot.last_cmd == "A45.0"

    bot.ready_for_next_turn = False
    bot.process_llm_response("S")
    assert bot.shield is True
    assert bot.last_cmd == "S"

    bot.ready_for_next_turn = False
    bot.process_llm_response("S1")
    assert bot.shield is True
    assert bot.last_cmd == "S1"

    bot.ready_for_next_turn = False
    bot.process_llm_response("S0")
    assert bot.shield is False
    assert bot.last_cmd == "S0"

    bot.ready_for_next_turn = False
    bot.process_llm_response("B")
    assert shots == [1]
    assert bot.last_cmd == "B"

    bot.ready_for_next_turn = False
    bot.process_llm_response("nonsense")
    assert bot.last_cmd == "ERR"

    assert completed == [1, 1, 1, 1, 1, 1, 1, 1]


def test_round_completion_and_session_save(monkeypatch, tmp_path: Path) -> None:
    board, scheduled_once, _history_log = _build_board(
        monkeypatch,
        overrides={
            ("game", "turns_per_round"): 1,
            ("game", "total_rounds"): 1,
        },
    )
    monkeypatch.setattr(
        board.ollama_connector,
        "send_prompt_to_llm_sync",
        lambda bot_id, **_kwargs: "S1" if bot_id == 1 else "S0",
    )

    board.submit_prompt_to_bot(1, "Reply with exactly S1")
    board.submit_prompt_to_bot(2, "Reply with exactly S0")

    _complete_scheduled_turn(scheduled_once, finalize_round=True)

    assert board.games_started == 2
    assert board.current_round == 0
    assert board.current_turn == 0
    assert len(board.history_manager.games) >= 2

    session_path = tmp_path / "session.json"
    board.history_manager.save_session(session_path)
    saved = json.loads(session_path.read_text(encoding="utf-8"))

    assert saved["schema_version"] == 2
    assert saved["session_type"] == "batllm_saved_session"
    assert saved["games"][0]["rounds"][0]["turns"][0]["plays"]
    assert saved["games"][0]["rounds"][0]["gameplay_settings_snapshot"]["turns_per_round"] == 1
    assert len(saved["games"]) == 1
    assert validate_session_payload(saved) is saved


def test_round_end_history_spacing_separates_next_round(monkeypatch) -> None:
    board, scheduled_once, history_log = _build_board(
        monkeypatch,
        overrides={
            ("game", "turns_per_round"): 1,
            ("game", "total_rounds"): 2,
        },
    )
    monkeypatch.setattr(
        board.ollama_connector,
        "send_prompt_to_llm_sync",
        lambda _bot_id, **_kwargs: "S0",
    )

    board.submit_prompt_to_bot(1, "Reply with exactly S0")
    board.submit_prompt_to_bot(2, "Reply with exactly S0")

    _complete_scheduled_turn(scheduled_once, finalize_round=True)

    board.submit_prompt_to_bot(1, "Reply with exactly S0")
    board.submit_prompt_to_bot(2, "Reply with exactly S0")

    bot_one_entries = [text for bot_id, text in history_log if bot_id == 1]
    round_end_index = next(
        index for index, text in enumerate(bot_one_entries) if "Round 1 ended." in text
    )

    assert bot_one_entries[round_end_index - 1] == "\n"
    assert bot_one_entries[round_end_index + 1] == "\n\n"
    assert "Round 2" in bot_one_entries[round_end_index + 2]


def test_history_manager_exports_roundtrip_and_views(monkeypatch, tmp_path: Path) -> None:
    board, scheduled_once, _history_log = _build_board(monkeypatch, overrides={
        ("game", "turns_per_round"): 1,
    })
    monkeypatch.setattr(
        board.ollama_connector,
        "send_prompt_to_llm_sync",
        lambda bot_id, **_kwargs: "M" if bot_id == 1 else "B",
    )

    board.submit_prompt_to_bot(1, "Reply with exactly M")
    board.submit_prompt_to_bot(2, "Reply with exactly B")
    _complete_scheduled_turn(scheduled_once, finalize_round=True)

    history = board.history_manager.get_chat_history(shared=True)
    history_by_bot = {entry["bot_id"]: entry for entry in history}
    assert history_by_bot == {
        1: {"bot_id": 1, "llm_response": "M", "cmd": "M"},
        2: {"bot_id": 2, "llm_response": "B", "cmd": "B"},
    }

    text_dump = board.history_manager.to_text(include_messages=True)
    assert 'LLM Response: "M"' in text_dump
    assert "Command: B" in text_dump

    compact = board.history_manager.to_compact_text()
    assert "Game 1" in compact
    assert "Round 1" in compact
    assert 'Bot 2: llm "B" -> cmd="B"' in compact

    bot_compact = board.history_manager.to_compact_text_for_bot(1)
    assert "prompt:" in bot_compact
    assert "Reply with exactly M" in bot_compact
    assert "llm response:" in bot_compact
    assert "'M'" in bot_compact

    session_path = tmp_path / "session-roundtrip.json"
    board.history_manager.save_session(session_path)
    saved = json.loads(session_path.read_text(encoding="utf-8"))
    expected_games = list(board.history_manager.games)
    while len(expected_games) > 1 and not expected_games[-1].get("rounds"):
        expected_games.pop()
    normalized_games = json.loads(json.dumps(expected_games))
    assert saved["games"] == normalized_games


def test_manual_new_game_finalises_old_bots_before_replacement(monkeypatch) -> None:
    board, _scheduled_once, _history_log = _build_board(monkeypatch)
    board.history_manager.start_round(board)
    board.history_manager.start_turn(board)
    old_bots = list(board.bots)
    old_bots[0].health = 0
    old_bots[1].health = 37

    board.start_new_game()

    abandoned = board.history_manager.games[0]
    turn = abandoned["rounds"][0]["turns"][0]
    assert abandoned["winner"] == 2
    assert turn["post_state"][1]["health"] == 0
    assert turn["post_state"][2]["health"] == 37
    assert board.bots != old_bots


def test_new_game_replaces_connector_history_generation(monkeypatch) -> None:
    board, _scheduled_once, _history_log = _build_board(monkeypatch)
    retired_connector = board.ollama_connector
    retired_connector._history_shared = [{"role": "user", "content": "old game"}]

    board.start_new_game()

    assert board.ollama_connector is not retired_connector
    assert board.ollama_connector._history_shared == []
    retired_connector._history_shared.append(
        {"role": "assistant", "content": "late"}
    )
    assert board.ollama_connector._history_shared == []


def test_active_round_rejects_new_prompt_submissions(monkeypatch) -> None:
    board, scheduled_once, _history_log = _build_board(monkeypatch)
    board.submit_prompt_to_bot(1, "first")
    board.submit_prompt_to_bot(2, "second")
    active_round = board.history_manager.current_round
    queued = list(scheduled_once)

    assert board.submit_prompt_to_bot(1, "replacement") is False
    assert board.history_manager.current_round is active_round
    assert scheduled_once == queued
    assert board.get_bot_by_id(1).current_prompt == "first"


def test_cancellation_reuses_active_turn_number_after_completed_turn(monkeypatch) -> None:
    board, _scheduled_once, _history_log = _build_board(monkeypatch)
    manager = board.history_manager
    manager.start_round(board)
    manager.start_turn(board)
    manager.end_turn(board)
    manager.start_turn(board)
    rollback_state = manager.current_round["initial_state"]

    manager.cancel_round("cancelled", rollback_state=rollback_state)

    turns = manager.games[0]["rounds"][0]["turns"]
    assert [turn["turn"] for turn in turns] == [1, 2]
    assert turns[1]["post_state"] == rollback_state


def test_home_screen_save_session_file_uses_configured_folder(monkeypatch, tmp_path: Path) -> None:
    board, scheduled_once, _history_log = _build_board(monkeypatch, overrides={
        ("game", "turns_per_round"): 1,
    })
    monkeypatch.setattr(
        board.ollama_connector,
        "send_prompt_to_llm_sync",
        lambda bot_id, **_kwargs: "S1" if bot_id == 1 else "S0",
    )
    board.submit_prompt_to_bot(1, "Reply with exactly S1")
    board.submit_prompt_to_bot(2, "Reply with exactly S0")
    _complete_scheduled_turn(scheduled_once, finalize_round=True)

    screen = HomeScreen()
    screen.ids = {"game_board": board}
    original_get = config.get
    monkeypatch.setattr(
        config,
        "get",
        lambda section, key: str(tmp_path / "saved-sessions")
        if (section, key) == ("data", "saved_sessions_folder")
        else original_get(section, key),
    )

    screen._save_session_file("history-export")

    exported = tmp_path / "saved-sessions" / "history-export.json"
    assert exported.exists()
    saved = json.loads(exported.read_text(encoding="utf-8"))
    assert saved["games"][0]["rounds"][0]["prompts"][0]["prompt"] == "Reply with exactly S1"


def test_home_screen_requires_confirmation_before_overwrite(monkeypatch, tmp_path: Path) -> None:
    board, scheduled_once, _history_log = _build_board(
        monkeypatch, overrides={("game", "turns_per_round"): 1}
    )
    monkeypatch.setattr(
        board.ollama_connector,
        "send_prompt_to_llm_sync",
        lambda bot_id, **_kwargs: "S1" if bot_id == 1 else "S0",
    )
    board.submit_prompt_to_bot(1, "one")
    board.submit_prompt_to_bot(2, "two")
    _complete_scheduled_turn(scheduled_once, finalize_round=True)
    screen = HomeScreen()
    screen.ids = {"game_board": board}
    original_get = config.get
    monkeypatch.setattr(
        config,
        "get",
        lambda section, key: str(tmp_path)
        if (section, key) == ("data", "saved_sessions_folder")
        else original_get(section, key),
    )
    target = tmp_path / "existing.json"
    target.write_text("original", encoding="utf-8")
    prompts = []
    monkeypatch.setattr(
        screen,
        "_show_confirmation_popup",
        lambda title, message, confirm: prompts.append((title, message, confirm)),
    )

    assert screen._save_session_file("existing.json") is False
    assert target.read_text(encoding="utf-8") == "original"
    assert prompts[0][0] == "Replace Session"

    prompts[0][2]()
    assert target.read_text(encoding="utf-8") != "original"


def test_session_export_filters_all_incomplete_games_and_rounds(
    monkeypatch, tmp_path: Path
) -> None:
    board, scheduled_once, _history_log = _build_board(
        monkeypatch, overrides={("game", "turns_per_round"): 1}
    )
    manager = board.history_manager
    manager.start_round(board)
    board.start_new_game()
    monkeypatch.setattr(
        board.ollama_connector,
        "send_prompt_to_llm_sync",
        lambda _bot_id, **_kwargs: "S0",
    )
    board.submit_prompt_to_bot(1, "one")
    board.submit_prompt_to_bot(2, "two")
    _complete_scheduled_turn(scheduled_once, finalize_round=True)
    manager.start_round(board)

    target = tmp_path / "sanitised.json"
    manager.save_session(target)
    payload = json.loads(target.read_text(encoding="utf-8"))

    assert len(payload["games"]) == 1
    assert len(payload["games"][0]["rounds"]) == 1
    assert payload["games"][0]["rounds"][0]["turns"]


def test_session_export_rejects_session_without_completed_turn(
    monkeypatch, tmp_path: Path
) -> None:
    board, _scheduled_once, _history_log = _build_board(monkeypatch)

    with pytest.raises(ValueError, match="no completed turn"):
        board.history_manager.save_session(tmp_path / "empty.json")

    assert not (tmp_path / "empty.json").exists()


def test_home_screen_save_failure_is_reported_and_does_not_exit(
    monkeypatch, tmp_path: Path
) -> None:
    screen = HomeScreen()
    saved_callbacks = []
    alerts = []

    def fail_save(_path):
        raise PermissionError("read-only folder")

    screen.ids = {
        "game_board": SimpleNamespace(
            history_manager=SimpleNamespace(save_session=fail_save)
        )
    }
    original_get = config.get
    monkeypatch.setattr(
        config,
        "get",
        lambda section, key: str(tmp_path)
        if (section, key) == ("data", "saved_sessions_folder")
        else original_get(section, key),
    )
    monkeypatch.setattr(
        "view.home_screen.show_fading_alert",
        lambda title, message, **_kwargs: alerts.append((title, message)),
    )

    assert (
        screen._save_session_file(
            "failed", on_saved=lambda: saved_callbacks.append(True)
        )
        is False
    )
    assert saved_callbacks == []
    assert alerts[0][0] == "Session not saved"


def test_round_settings_snapshot_is_frozen_per_round(monkeypatch) -> None:
    overrides = {
        ("game", "turns_per_round"): 1,
        ("game", "total_rounds"): 2,
        ("game", "bullet_damage"): 5,
        ("game", "bullet_diameter"): 0.02,
        ("game", "shield_size"): 70,
    }
    board, scheduled_once, _history_log = _build_board(monkeypatch, overrides=overrides)
    monkeypatch.setattr(
        board.ollama_connector,
        "send_prompt_to_llm_sync",
        lambda _bot_id, **_kwargs: "S0",
    )

    board.submit_prompt_to_bot(1, "Reply with exactly S0")
    board.submit_prompt_to_bot(2, "Reply with exactly S0")

    first_snapshot = board.history_manager.current_round["gameplay_settings_snapshot"]
    assert first_snapshot["bullet_damage"] == 5
    assert first_snapshot["bullet_diameter"] == pytest.approx(0.02)
    assert first_snapshot["shield_size"] == 70

    overrides[("game", "bullet_damage")] = 9
    overrides[("game", "bullet_diameter")] = 0.05
    overrides[("game", "shield_size")] = 33

    assert board.current_round_settings.bullet_damage == 5
    assert board.current_round_settings.bullet_diameter == pytest.approx(0.02)
    assert board.current_round_settings.shield_size == 70

    _complete_scheduled_turn(scheduled_once, finalize_round=True)

    board.submit_prompt_to_bot(1, "Reply with exactly S0")
    board.submit_prompt_to_bot(2, "Reply with exactly S0")

    second_snapshot = board.history_manager.current_round["gameplay_settings_snapshot"]
    assert second_snapshot["bullet_damage"] == 9
    assert second_snapshot["bullet_diameter"] == pytest.approx(0.05)
    assert second_snapshot["shield_size"] == 33


def test_bullet_uses_configured_diameter(monkeypatch) -> None:
    original_get = config.get
    monkeypatch.setattr(
        config,
        "get",
        lambda section, key: 0.05
        if (section, key) == ("game", "bullet_diameter")
        else original_get(section, key),
    )

    bullet = Bullet(1, 0.5, 0.5, 0)

    assert bullet.diameter == pytest.approx(0.05)



def test_completed_game_restart_replaces_connector_history_generation(monkeypatch) -> None:
    board, _scheduled_once, _history_log = _build_board(monkeypatch)
    retired_connector = board.ollama_connector
    retired_connector._history_shared = [{"role": "user", "content": "old game"}]

    board.end_game()
    assert board.history_manager.current_game is None
    board.start_new_game()

    assert board.ollama_connector is not retired_connector
    assert board.ollama_connector._history_shared == []


def test_session_export_drops_active_and_cancelled_turns(monkeypatch, tmp_path: Path) -> None:
    board, scheduled_once, _history_log = _build_board(
        monkeypatch, overrides={("game", "turns_per_round"): 1}
    )
    manager = board.history_manager
    monkeypatch.setattr(
        board.ollama_connector,
        "send_prompt_to_llm_sync",
        lambda _bot_id, **_kwargs: "S0",
    )
    board.submit_prompt_to_bot(1, "one")
    board.submit_prompt_to_bot(2, "two")
    _complete_scheduled_turn(scheduled_once, finalize_round=True)

    manager.start_round(board)
    manager.start_turn(board)
    active_target = tmp_path / "active-filtered.json"
    manager.save_session(active_target)
    active_payload = json.loads(active_target.read_text(encoding="utf-8"))
    assert len(active_payload["games"][0]["rounds"]) == 1
    assert len(active_payload["games"][0]["rounds"][0]["turns"]) == 1

    manager.cancel_round("cancelled", rollback_state=manager.games[0]["rounds"][0]["initial_state"])
    cancelled_target = tmp_path / "cancelled-filtered.json"
    manager.save_session(cancelled_target)
    cancelled_payload = json.loads(cancelled_target.read_text(encoding="utf-8"))
    assert len(cancelled_payload["games"][0]["rounds"]) == 1
    assert len(cancelled_payload["games"][0]["rounds"][0]["turns"]) == 1


def test_debug_llm_shortcut_submits_to_both_valid_bot_ids(monkeypatch) -> None:
    board, _scheduled_once, _history_log = _build_board(monkeypatch)
    submitted = []
    monkeypatch.setenv("BATLLM_DEBUG_SHORTCUTS", "1")
    monkeypatch.setattr(
        board,
        "submit_prompt_to_bot",
        lambda bot_id, prompt: submitted.append((bot_id, prompt)) or True,
    )

    assert board._on_keyboard_down(_FakeKeyboard(), (0, "l"), "", []) is True
    assert [bot_id for bot_id, _prompt in submitted] == [1, 2]


def test_state_validation_rejects_key_id_mismatch_and_duplicate_ids() -> None:
    from game.replay_engine import validate_state_map

    state = {
        "id": 1,
        "health": 30,
        "x": 0.2,
        "y": 0.5,
        "rot": 0,
        "shield": False,
    }
    mismatched = {"1": {**state, "id": 2}}
    with pytest.raises(ValueError, match="does not match embedded id"):
        validate_state_map(mismatched, require_id=True)

    duplicated = {"1": dict(state), 1: dict(state)}
    with pytest.raises(ValueError, match="duplicate bot id"):
        validate_state_map(duplicated, require_id=True)
