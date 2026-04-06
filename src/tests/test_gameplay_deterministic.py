from __future__ import annotations

import json
import math
from pathlib import Path
from types import SimpleNamespace

import pytest

from configs.app_config import config
from game.bot import Bot
from game.game_board import GameBoard
from game.ollama_connector import LLMTimeoutError, OllamaConnector
from game.prompt_store import PromptStore
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
    scheduled_once.pop(0)(0)

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

    scheduled_once.pop(0)(0)
    scheduled_once.pop(0)(0)

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

    scheduled_once.pop(0)(0)

    round_entry = board.history_manager.games[0]["rounds"][0]
    cancelled_turn = round_entry["turns"][0]

    assert round_entry["status"] == "cancelled"
    assert round_entry["cancelled_by_bot_id"] == 2
    assert cancelled_turn["status"] == "cancelled"
    assert cancelled_turn["plays"] == []
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

    scheduled_once.pop(0)(0)
    scheduled_once.pop(0)(0)

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
    scheduled_once.pop(0)(0)
    board.history_manager.end_round()

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
    normalized_games = json.loads(json.dumps(board.history_manager.games))
    assert saved["games"] == normalized_games


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
    scheduled_once.pop(0)(0)
    board.history_manager.end_round()

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


def test_round_settings_snapshot_is_frozen_per_round(monkeypatch) -> None:
    overrides = {
        ("game", "turns_per_round"): 1,
        ("game", "total_rounds"): 2,
        ("game", "bullet_damage"): 5,
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
    assert first_snapshot["shield_size"] == 70

    overrides[("game", "bullet_damage")] = 9
    overrides[("game", "shield_size")] = 33

    assert board.current_round_settings.bullet_damage == 5
    assert board.current_round_settings.shield_size == 70

    scheduled_once.pop(0)(0)
    scheduled_once.pop(0)(0)

    board.submit_prompt_to_bot(1, "Reply with exactly S0")
    board.submit_prompt_to_bot(2, "Reply with exactly S0")

    second_snapshot = board.history_manager.current_round["gameplay_settings_snapshot"]
    assert second_snapshot["bullet_damage"] == 9
    assert second_snapshot["shield_size"] == 33
