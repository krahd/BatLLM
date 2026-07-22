"""Headless BatLLM runtime for auditable human--LLM-mediated control.

The module records the exact model invocation, preserves or commits to the
provider response according to the selected privacy mode, grounds the response
to BatLLM's command language, and applies that command through the same pure
transition semantics used by the verifier.
"""
# pylint: disable=too-many-arguments,too-many-instance-attributes,broad-exception-caught

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from time import perf_counter
from typing import Any, Mapping, Protocol

from game.replay_engine import GameplaySettingsSnapshot, apply_play, normalize_state_map
from game.session_v3 import build_session_v3
from game.trace_contract import (
    PrivacyMode,
    event_to_dict,
    finalise_play_hash,
    new_id,
    protect_text,
    store_request_payload,
    transition_hash,
    utc_now_iso,
)


class ChatClient(Protocol):
    """Minimal provider-neutral chat interface."""

    def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        options: dict[str, Any],
        stream: bool = False,
    ) -> Any: ...


@dataclass(frozen=True)
class InvocationPolicy:
    """Model invocation settings frozen into every request payload."""

    provider: str = "ollama"
    model: str = "smollm2"
    endpoint: str = "http://localhost:11434/api/chat"
    options: Mapping[str, Any] | None = None
    max_attempts: int = 2


@dataclass(frozen=True)
class InvocationOutcome:
    """Provider-neutral result of one request, including terminal failures."""

    response_text: str | None
    attempts: int
    latency_ms: float
    started_at: str
    completed_at: str
    error_type: str | None = None
    error_message: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.error_type is None


def extract_response_text(response: Any) -> str:
    """Extract text from strings, Modelito/Ollama objects, or dictionaries."""

    if isinstance(response, str):
        text = response
    else:
        text = ""
        try:
            text = response.message.content  # type: ignore[attr-defined]
        except Exception:
            if isinstance(response, Mapping):
                message = response.get("message")
                if isinstance(message, Mapping):
                    text = str(message.get("content") or "")
                elif isinstance(response.get("response"), str):
                    text = str(response["response"])
    text = str(text or "")
    if not text.strip():
        raise RuntimeError(f"Empty model response ({type(response).__name__}).")
    return text


class ScriptedClient:
    """Deterministic client used by examples, tests, and the evaluation corpus."""

    def __init__(self, commands: list[str] | tuple[str, ...]):
        if not commands:
            raise ValueError("ScriptedClient requires at least one command.")
        self.commands = [str(command) for command in commands]
        self.index = 0
        self.requests: list[dict[str, Any]] = []

    def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        options: dict[str, Any],
        stream: bool = False,
    ) -> str:
        self.requests.append(
            {
                "model": model,
                "messages": deepcopy(messages),
                "options": deepcopy(options),
                "stream": bool(stream),
            }
        )
        command = self.commands[self.index % len(self.commands)]
        self.index += 1
        return command


class ModelitoChatClient:
    """Optional adapter for local Ollama models through Modelito."""

    def __init__(self, *, host: str = "http://localhost", port: int = 11434):
        try:
            from modelito import Client, Message, OllamaProvider
        except Exception as exc:  # pragma: no cover - optional live integration
            raise RuntimeError(
                "Modelito is required for live Ollama research runs."
            ) from exc
        self._Message = Message
        self._provider = OllamaProvider(host=host, port=port)
        self._client = Client(provider=self._provider)

    def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        options: dict[str, Any],
        stream: bool = False,
    ) -> str:
        self._provider.model = model
        self._client.model = model
        converted = [
            self._Message(role=message["role"], content=message["content"])
            for message in messages
        ]
        if stream:
            return "".join(self._client.stream(converted, settings=options))
        return self._client.summarize(converted, settings=options)


class MediatedGameRuntime:
    """Record exact invocations and replayable transitions for BatLLM."""

    def __init__(
        self,
        *,
        client: ChatClient,
        initial_state: Mapping[Any, Mapping[str, Any]],
        rules: GameplaySettingsSnapshot,
        policy: InvocationPolicy | None = None,
        system_instructions: str = "",
        prompt_augmentation: bool = True,
        independent_contexts: bool = True,
        privacy_mode: PrivacyMode | str = PrivacyMode.FULL,
        app_version: str = "0.3.6",
        git_commit: str | None = None,
        model_provenance: Mapping[str, Any] | None = None,
    ) -> None:
        self.client = client
        self.state = normalize_state_map(initial_state)
        self.rules = rules
        self.policy = policy or InvocationPolicy()
        self.system_instructions = str(system_instructions)
        self.prompt_augmentation = bool(prompt_augmentation)
        self.independent_contexts = bool(independent_contexts)
        self.privacy_mode = PrivacyMode(privacy_mode)
        self.app_version = app_version
        self.git_commit = git_commit
        self.model_provenance = dict(model_provenance or {})
        self.model_provenance.setdefault("provider", self.policy.provider)
        self.model_provenance.setdefault("requested_model", self.policy.model)
        self.model_provenance.setdefault("endpoint", self.policy.endpoint)
        self._shared_history: list[dict[str, str]] = []
        self._history_by_bot: dict[int, list[dict[str, str]]] = {}
        self._previous_play_sha256: str | None = None
        self._sequence = 0
        self._rounds: list[dict[str, Any]] = []
        self._active_round: dict[str, Any] | None = None

    def _history(self, bot_id: int) -> list[dict[str, str]]:
        history = (
            self._history_by_bot.setdefault(int(bot_id), [])
            if self.independent_contexts
            else self._shared_history
        )
        if self.system_instructions:
            system_message = {"role": "system", "content": self.system_instructions}
            if not history or history[0].get("role") != "system":
                history.insert(0, system_message)
            elif history[0] != system_message:
                history[0] = system_message
        return history

    def _user_content(self, prompt: str) -> tuple[str, dict[str, Any]]:
        game_state = {"bots": deepcopy(self.state)}
        if self.prompt_augmentation:
            rendered = (
                "[GAME_STATE]\n"
                + json.dumps(
                    game_state,
                    separators=(",", ":"),
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n[PLAYER_INPUT]\n"
                + prompt
            )
        else:
            rendered = prompt
        return rendered, game_state

    def start_round(
        self, prompts: Mapping[int, str] | None = None
    ) -> dict[str, Any]:
        if self._active_round is not None:
            raise RuntimeError("A round is already active.")
        round_entry = {
            "round": len(self._rounds) + 1,
            "started_at": utc_now_iso(),
            "gameplay_settings_snapshot": self.rules.to_dict(),
            "initial_state": deepcopy(self.state),
            "prompts": [
                {
                    "bot_id": int(bot_id),
                    "prompt": protect_text(prompt, self.privacy_mode),
                }
                for bot_id, prompt in sorted((prompts or {}).items())
            ],
            "plays": [],
        }
        self._rounds.append(round_entry)
        self._active_round = round_entry
        return round_entry

    def end_round(self) -> dict[str, Any]:
        if self._active_round is None:
            raise RuntimeError("No round is active.")
        self._active_round["ended_at"] = utc_now_iso()
        self._active_round["final_state"] = deepcopy(self.state)
        completed = self._active_round
        self._active_round = None
        return completed

    def _invoke(self, request_payload: dict[str, Any]) -> InvocationOutcome:
        attempts = 0
        started_at = utc_now_iso()
        started = perf_counter()
        last_error: BaseException | None = None
        for attempts in range(1, max(1, self.policy.max_attempts) + 1):
            try:
                response = self.client.chat(
                    model=request_payload["model"],
                    messages=deepcopy(request_payload["messages"]),
                    options=deepcopy(request_payload["options"]),
                    stream=False,
                )
                return InvocationOutcome(
                    response_text=extract_response_text(response),
                    attempts=attempts,
                    latency_ms=(perf_counter() - started) * 1000.0,
                    started_at=started_at,
                    completed_at=utc_now_iso(),
                )
            except Exception as exc:  # provider-neutral retry boundary
                last_error = exc
        assert last_error is not None
        return InvocationOutcome(
            response_text=None,
            attempts=attempts,
            latency_ms=(perf_counter() - started) * 1000.0,
            started_at=started_at,
            completed_at=utc_now_iso(),
            error_type=type(last_error).__name__,
            error_message=str(last_error),
        )

    def play(self, *, bot_id: int, human_prompt: str) -> dict[str, Any]:
        if self._active_round is None:
            self.start_round({int(bot_id): human_prompt})
        self._sequence += 1
        pre_state = deepcopy(self.state)
        rendered, game_state = self._user_content(str(human_prompt))
        history = self._history(int(bot_id))
        user_message = {"role": "user", "content": rendered}
        history.append(user_message)
        request_payload = {
            "provider": self.policy.provider,
            "endpoint": self.policy.endpoint,
            "model": self.policy.model,
            "messages": deepcopy(history),
            "options": dict(self.policy.options or {}),
            "stream": False,
        }
        outcome = self._invoke(request_payload)
        if outcome.succeeded:
            raw_response = str(outcome.response_text)
            history.append({"role": "assistant", "content": raw_response})
            command_source = raw_response
            status = "ok"
            error_record = None
        else:
            if history and history[-1] is user_message:
                history.pop()
            raw_response = ""
            command_source = "ERR"
            status = "invocation-error"
            error_record = {
                "type": outcome.error_type,
                "message": protect_text(outcome.error_message, self.privacy_mode),
            }

        resolution = apply_play(
            pre_state,
            bot_id=int(bot_id),
            llm_response=command_source,
            cmd_text=None,
            rules=self.rules,
        )
        self.state = normalize_state_map(resolution.state_by_bot)
        events = [event_to_dict(event) for event in resolution.events]
        command = resolution.normalized_cmd
        if status == "ok" and command == "ERR":
            status = "invalid-command"
        transition_sha = transition_hash(
            bot_id=int(bot_id),
            pre_state=pre_state,
            command=command,
            rules=self.rules.to_dict(),
            post_state=self.state,
            events=events,
        )
        play: dict[str, Any] = {
            "play_id": new_id("play"),
            "sequence": self._sequence,
            "bot_id": int(bot_id),
            "human_prompt": protect_text(human_prompt, self.privacy_mode),
            "system_instructions": protect_text(
                self.system_instructions, self.privacy_mode
            ),
            "context_policy": {
                "prompt_augmentation": self.prompt_augmentation,
                "independent_contexts": self.independent_contexts,
            },
            "game_state_supplied_to_model": deepcopy(game_state),
            "request": store_request_payload(request_payload, self.privacy_mode),
            "request_started_at": outcome.started_at,
            "request_completed_at": outcome.completed_at,
            "latency_ms": outcome.latency_ms,
            "attempts": outcome.attempts,
            "response": protect_text(raw_response, self.privacy_mode),
            "normalized_command": command,
            "events": events,
            "pre_state": pre_state,
            "post_state": deepcopy(self.state),
            "transition_sha256": transition_sha,
            "status": status,
        }
        if error_record is not None:
            play["error"] = error_record
        play = finalise_play_hash(play, self._previous_play_sha256)
        self._previous_play_sha256 = play["play_sha256"]
        assert self._active_round is not None
        self._active_round["plays"].append(play)
        return play

    def run_turn(
        self,
        prompts: Mapping[int, str],
        *,
        order: list[int] | tuple[int, ...] | None = None,
    ) -> list[dict[str, Any]]:
        selected_order = list(order or sorted(prompts))
        return [
            self.play(bot_id=bot_id, human_prompt=prompts[bot_id])
            for bot_id in selected_order
        ]

    def session_payload(self) -> dict[str, Any]:
        if self._active_round is not None:
            self.end_round()
        games = [
            {
                "game_id": 1,
                "started_at": (
                    self._rounds[0]["started_at"]
                    if self._rounds
                    else utc_now_iso()
                ),
                "rounds": deepcopy(self._rounds),
                "final_state": deepcopy(self.state),
            }
        ]
        return build_session_v3(
            games=games,
            app_version=self.app_version,
            privacy_mode=self.privacy_mode,
            git_commit=self.git_commit,
            model_provenance=self.model_provenance,
        )
