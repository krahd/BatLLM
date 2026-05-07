"""Ollama configuration and model-management screen."""

from __future__ import annotations

from datetime import datetime
import json
import subprocess
import sys
import threading
import os
from pathlib import Path
from typing import Any

from llm import service as ollama_service
from modelito import ollama_service as modelito_ollama_service
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen

from configs.app_config import config
from util.utils import (
    show_confirmation_dialog,
    show_fading_alert,
    show_text_input_dialog,
    switch_screen,
)


ROOT = Path(__file__).resolve().parents[2]


def build_ollama_install_command(platform_name: str | None = None) -> list[str]:
    """Return the platform-specific Ollama install command."""
    command, _display = ollama_service.install_command_for_current_platform(platform_name)
    return command


def describe_ollama_install_command(platform_name: str | None = None) -> str:
    """Return a human-readable description of the install command."""
    _command, display = ollama_service.install_command_for_current_platform(platform_name)
    return display


class OllamaConfigScreen(Screen):
    """Manage the local Ollama service and BatLLM model selection."""

    status_text = StringProperty("Idle")
    status_details = StringProperty("Ollama status has not been checked yet.")
    output_log = StringProperty("")
    local_models = ListProperty([])
    remote_models = ListProperty([])
    selected_local_model = StringProperty("")
    selected_remote_model = StringProperty("")
    selected_local_model_label = StringProperty("Select local model")
    selected_local_timeout_text = StringProperty("")
    selected_local_timeout_details = StringProperty("Select a local model to edit its timeout.")
    warmup_timeout_text = StringProperty("")
    warmup_timeout_details = StringProperty(
        "Configure how long BatLLM waits for Ollama to finish starting.")
    selected_remote_model_label = StringProperty("Select remote model")
    selected_remote_timeout_details = StringProperty(
        "Select a remote model to see its estimated timeout."
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._local_model_entries: list[dict[str, str]] = []
        self._remote_model_entries: list[dict[str, str]] = []
        self._remote_model_display_map: dict[str, str] = {}
        self._model_picker_popup = None
        managed_model = str(config.get("llm", "last_served_model") or "").strip()
        self._managed_model_name: str | None = managed_model or None

    def on_pre_enter(self, *_args):
        Window.unbind(on_key_down=self.handle_window_key_down)
        Window.bind(on_key_down=self.handle_window_key_down)
        self._refresh_warmup_timeout()
        self.refresh_ollama_status()
        self.refresh_local_models()

    def on_pre_leave(self, *_args):
        Window.unbind(on_key_down=self.handle_window_key_down)

    def handle_window_key_down(self, _window, key, *_args):
        """Handle Escape by dismissing the model picker or returning to Settings."""
        if key != 27:
            return False

        if self._dismiss_model_picker():
            return True

        self.go_to_settings_screen()
        return True

    def go_to_settings_screen(self):
        switch_screen(self.manager, "settings", direction="right")

    def _llm_endpoint(self) -> tuple[str, int]:
        url = str(config.get("llm", "url") or "http://localhost").rstrip("/")
        port = int(config.get("llm", "port") or 11434)
        return url, port

    def _chat_path(self) -> str:
        return str(config.get("llm", "path") or "/api/chat")

    def _llm_timeout_config(self, model_name: str | None = None) -> dict[str, Any]:
        selected_model = str(model_name or config.get("llm", "model") or "").strip()
        model_timeouts = config.get("llm", "model_timeouts")
        if not isinstance(model_timeouts, dict):
            model_timeouts = {}
        return {
            "model": selected_model,
            "model_timeouts": dict(model_timeouts),
            "timeout": config.get("llm", "timeout"),
        }

    def _warmup_timeout_config(self) -> dict[str, Any]:
        return {"warmup_timeout": config.get("llm", "warmup_timeout")}

    @staticmethod
    def _format_timeout_seconds(timeout_seconds: float) -> str:
        return f"{float(timeout_seconds):g}"

    @staticmethod
    def _timeout_source_text(source: str) -> str:
        return {
            "model_override": "saved per-model override",
            "global_override": "global timeout setting",
            "model_default": "BatLLM's common-model default",
            "fallback_default": "BatLLM's generic fallback",
        }.get(source, "BatLLM timeout settings")

    def _model_timeout_overrides(self) -> dict[str, Any]:
        model_timeouts = config.get("llm", "model_timeouts")
        return dict(model_timeouts) if isinstance(model_timeouts, dict) else {}

    def _save_model_timeout_overrides(self, overrides: dict[str, Any]):
        config.set("llm", "model_timeouts", overrides)
        config.save()

    def _remove_model_timeout_override(self, model_name: str) -> bool:
        overrides = self._model_timeout_overrides()
        if model_name not in overrides:
            return False
        del overrides[model_name]
        self._save_model_timeout_overrides(overrides)
        return True

    def _refresh_selected_local_timeout(self):
        model_name = self.selected_local_model.strip()
        if not model_name:
            self.selected_local_timeout_text = ""
            self.selected_local_timeout_details = "Select a local model to edit its timeout."
            return

        timeout_seconds, source = ollama_service.resolve_request_timeout_details(
            self._llm_timeout_config(model_name),
            model=model_name,
        )
        formatted = self._format_timeout_seconds(timeout_seconds)
        self.selected_local_timeout_text = formatted
        self.selected_local_timeout_details = (
            f"Effective timeout for {model_name}: {formatted}s from "
            f"{self._timeout_source_text(source)}."
        )

    def _set_local_selection(self, model_name: str):
        model_name = model_name.strip()
        self.selected_local_model = model_name
        self.selected_local_model_label = model_name or "Select local model"
        self._refresh_selected_local_timeout()

    def _refresh_warmup_timeout(self):
        timeout_seconds = ollama_service.resolve_warmup_timeout(self._warmup_timeout_config())
        configured = config.get("llm", "warmup_timeout")
        self.warmup_timeout_text = self._format_timeout_seconds(timeout_seconds)
        source = "saved warmup timeout override" if configured not in (
            None, "") else "BatLLM/modelito default"
        self.warmup_timeout_details = (
            f"Service warmup timeout: {self._format_timeout_seconds(timeout_seconds)}s from {source}."
        )

    def _set_remote_selection(self, model_name: str):
        model_name = model_name.strip()
        self.selected_remote_model = model_name
        self.selected_remote_model_label = (
            self._remote_model_display_map.get(model_name, model_name) or "Select remote model"
        )
        self._refresh_selected_remote_timeout()

    def _selected_remote_entry(self) -> dict[str, str] | None:
        model_name = self.selected_remote_model.strip()
        if not model_name:
            return None

        for entry in self._remote_model_entries:
            if entry.get("name") == model_name:
                return entry
        return None

    def _refresh_selected_remote_timeout(self):
        entry = self._selected_remote_entry()
        if entry is None:
            self.selected_remote_timeout_details = (
                "Select a remote model to see its estimated timeout."
            )
            return

        timeout_seconds, source = ollama_service.estimate_remote_model_timeout_details(
            entry.get("name", ""),
            size_label=entry.get("size", ""),
        )
        formatted = self._format_timeout_seconds(timeout_seconds)
        self.selected_remote_timeout_details = (
            f"Estimated timeout for {entry.get('display') or entry.get('name')}: "
            f"{formatted}s from {source}."
        )

    def _set_status(self, text: str):
        Clock.schedule_once(lambda *_: setattr(self, "status_text", text), 0)

    def _set_status_details(self, text: str):
        Clock.schedule_once(lambda *_: setattr(self, "status_details", text), 0)

    def _append_log(self, text: str):
        clean = text.strip()
        if not clean:
            return

        timestamp = datetime.now().strftime("%H:%M:%S")

        def update(*_):
            entry = f"[{timestamp}] {clean}"
            self.output_log = f"{self.output_log}\n\n{entry}" if self.output_log else entry

        Clock.schedule_once(update, 0)

    def _run_in_thread(self, fn):
        threading.Thread(target=fn, daemon=True).start()

    def _schedule_ui_callback(self, callback):
        if callback is None:
            return

        Clock.schedule_once(lambda *_: callback(), 0)

    def _dismiss_model_picker(self) -> bool:
        """Dismiss the active model picker popup, if one is open."""
        if self._model_picker_popup is None:
            return False

        self._model_picker_popup.dismiss()
        return True

    def _show_model_picker(
        self,
        *,
        title: str,
        entries: list[dict[str, str]],
        selected_value: str,
        on_select,
    ):
        """Show a modal list of selectable models."""
        if self._model_picker_popup is not None:
            self._model_picker_popup.dismiss()
            self._model_picker_popup = None

        if not entries:
            show_fading_alert(title, "No models available.", duration=1.5, fade_duration=1.0)
            return

        layout = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(12))
        scroll = ScrollView(
            do_scroll_x=False,
            scroll_type=["bars", "content"],
            bar_width=dp(10),
        )
        items = GridLayout(cols=1, spacing=0, size_hint_y=None)
        items.bind(minimum_height=items.setter("height"))

        popup = Popup(
            title=title,
            content=layout,
            size_hint=(0.82, 0.82),
            auto_dismiss=True,
        )

        def choose(model_name: str):
            popup.dismiss()
            on_select(model_name)

        for entry in entries:
            button = Button(
                text=entry["display"],
                size_hint_y=None,
                height=dp(46),
                halign="left",
                valign="middle",
                background_normal="",
                background_down="",
                shorten=True,
                background_color=(0.22, 0.38, 0.56, 1)
                if entry["name"] == selected_value
                else (0.12, 0.12, 0.12, 1),
                color=(1, 1, 1, 1),
            )
            button.bind(size=lambda inst, *_: setattr(inst,
                        "text_size", (inst.width - dp(16), None)))
            button.bind(on_release=lambda *_args, value=entry["name"]: choose(value))
            items.add_widget(button)

        scroll.add_widget(items)
        layout.add_widget(scroll)

        close_button = Button(
            text="Close",
            size_hint_y=None,
            height=dp(44),
            background_color=(0.85, 0.85, 0.85, 1),
            color=(0, 0, 0, 1),
        )
        close_button.bind(on_release=lambda *_: popup.dismiss())
        layout.add_widget(close_button)

        popup.bind(on_dismiss=lambda *_: setattr(self, "_model_picker_popup", None))
        self._model_picker_popup = popup
        popup.open()

    def _run_ollama_helper(self, action: str, *args: str) -> subprocess.CompletedProcess:
        # Ensure the child Python process can import the local `llm` package by
        # setting PYTHONPATH to include the repository `src` directory.
        env = os.environ.copy()
        src_path = str(ROOT / "src")
        existing = env.get("PYTHONPATH")
        env["PYTHONPATH"] = src_path + (os.pathsep + existing if existing else "")
        return subprocess.run(
            [sys.executable, "-m", "llm.service", action, *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )

    def _run_ollama_command(self, *args: str) -> subprocess.CompletedProcess:
        command = ollama_service.resolve_ollama_command()
        return subprocess.run(
            [command, *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def _run_ollama_install_command(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            build_ollama_install_command(),
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def _remember_served_model(self, model_name: str):
        model_name = model_name.strip()
        if not model_name:
            return
        if str(config.get("llm", "last_served_model") or "").strip() == model_name:
            return
        config.set("llm", "last_served_model", model_name)
        config.save()

    def _list_local_models_via_modelito(self) -> list[str]:
        return [name for name in ollama_service.list_local_models() if str(name).strip()]

    def _list_remote_model_catalog_via_modelito(self) -> list[dict[str, str]]:
        entries = []
        for entry in ollama_service.list_remote_model_catalog():
            display = entry.name
            if entry.installed:
                display = f"{display} (installed)"
            entries.append({"name": entry.name, "display": display, "size": ""})
        return entries

    def _running_model_names_via_modelito(self) -> list[str]:
        base_url, port = self._llm_endpoint()
        host = f"{base_url.removeprefix('http://').removeprefix('https://')}:{port}"
        return ollama_service.running_model_names(host)

    def _preload_model_via_modelito(self, model_name: str) -> dict[str, Any]:
        base_url, port = self._llm_endpoint()
        request_timeout = ollama_service.resolve_request_timeout(
            self._llm_timeout_config(model_name),
            model=model_name,
        )
        ollama_service.preload_model(base_url, port, model_name, timeout=request_timeout)
        self._append_log(
            f"modelito preload_model({base_url}, {port}, {model_name}, timeout={request_timeout:g})"
        )
        return {"ok": True}

    def _stop_serving_model_via_modelito(self, model_name: str) -> dict[str, Any]:
        base_url, port = self._llm_endpoint()
        host = f"{base_url.removeprefix('http://').removeprefix('https://')}:{port}"
        proc = ollama_service.run_ollama_command("stop", model_name, host=host)
        combined = ((proc.stdout or "") + (proc.stderr or "")).strip()
        self._append_log(f"$ ollama stop {model_name}\n{combined or f'exit {proc.returncode}'}")
        if proc.returncode != 0:
            raise RuntimeError(combined or f"Failed to stop model {model_name}")
        return {"ok": True}

    def _ensure_model_serving_via_modelito(self, model_name: str) -> dict[str, Any]:
        base_url, port = self._llm_endpoint()
        request_timeout = ollama_service.resolve_request_timeout(
            self._llm_timeout_config(model_name),
            model=model_name,
        )
        result = ollama_service.ensure_model_ready_detailed(
            model_name,
            host=base_url,
            port=port,
            auto_start=True,
            allow_download=False,
            timeout=request_timeout,
        )
        if not result.success:
            detail = result.error or result.message or "Model readiness check failed"
            raise RuntimeError(detail)
        self._append_log(
            f"modelito ensure_model_ready_detailed -> phase={result.phase} elapsed={result.elapsed_seconds:.2f}s message={result.message or 'ready'} source={result.source}"
        )
        return {"ready": True}

    def _pull_model_via_modelito(self, model_name: str):
        for state in ollama_service.download_model_progress(model_name, timeout=600.0):
            status = state.message or state.phase or "working"
            self._set_status(f"Pull {model_name}: {status}")
            self._append_log(
                f"modelito download_model_progress -> phase={state.phase} progress={state.progress} message={status}"
            )

    def _delete_model_via_modelito(self, model_name: str):
        ok = ollama_service.delete_model(model_name)
        self._append_log(f"modelito delete_model({model_name}) -> {ok}")
        if not ok:
            raise RuntimeError(f"Failed to delete model {model_name}")

    def _collect_ollama_status(self) -> dict[str, Any]:
        state = ollama_service.inspect_service_state()
        base_url, port = self._llm_endpoint()
        warmup_timeout = ollama_service.resolve_warmup_timeout(self._warmup_timeout_config())
        snapshot: dict[str, Any] = {
            "found": bool(state.get("installed")),
            "version": str(state.get("version") or "unknown"),
            "running": bool(state.get("running")),
            "server_version": str(state.get("version") or ""),
            "running_models": self._running_model_names_via_modelito() if state.get("running") else [],
            "configured_model": str(state.get("configured_model") or config.get("llm", "model") or ""),
            "endpoint": f"{base_url}:{port}",
            "warmup_timeout": warmup_timeout,
        }
        self._append_log(
            "modelito inspect_service_state -> "
            f"installed={snapshot['found']} running={snapshot['running']} version={snapshot['version']}"
        )
        if snapshot["running_models"]:
            self._append_log(
                f"modelito running_model_names -> {', '.join(snapshot['running_models'])}"
            )
        return snapshot

    def _format_status_report(self, snapshot: dict[str, Any]) -> str:
        lines = []
        configured_model = snapshot.get("configured_model") or "not set"

        if not snapshot.get("found"):
            lines.append("Ollama CLI: not found")
            lines.append("Installed version: unavailable")
            lines.append("Server status: not running")
            lines.append(f"BatLLM model: {configured_model}")
            lines.append(
                f"Warmup timeout: {self._format_timeout_seconds(snapshot.get('warmup_timeout') or 0)}s")
            return "\n".join(lines)

        lines.append("Ollama CLI: found")
        lines.append(f"Installed version: {snapshot.get('version') or 'unknown'}")
        lines.append(
            f"Warmup timeout: {self._format_timeout_seconds(snapshot.get('warmup_timeout') or 0)}s")

        if snapshot.get("running"):
            lines.append("Server status: running")
            running_models = snapshot.get("running_models") or []
            if running_models:
                lines.append(f"Running models: {', '.join(running_models)}")
            else:
                lines.append("Running models: none currently loaded")

            if configured_model != "not set":
                suffix = "(running)" if configured_model in running_models else "(configured, not currently running)"
                lines.append(f"BatLLM model: {configured_model} {suffix}")
            else:
                lines.append("BatLLM model: not set")
        else:
            lines.append("Server status: not running")
            lines.append(f"BatLLM model: {configured_model}")

        return "\n".join(lines)

    def refresh_ollama_status(self):
        self._set_status("Refreshing Ollama status...")

        def work():
            snapshot = self._collect_ollama_status()
            self._set_status_details(self._format_status_report(snapshot))

            if not snapshot.get("found"):
                self._set_status("Ollama not found.")
            elif snapshot.get("running"):
                self._set_status("Ollama is running.")
            else:
                self._set_status("Ollama is installed but not running.")

        self._run_in_thread(work)

    def request_install_ollama(self):
        self._set_status("Checking Ollama installation...")

        def work():
            snapshot = self._collect_ollama_status()
            installed = bool(snapshot.get("found"))
            title = "Reinstall Ollama" if installed else "Install Ollama"
            message = (
                "Ollama is already installed. Reinstall or update it using the official installer?"
                if installed
                else "Ollama is not installed. Install it now using the official Ollama installer?"
            )
            action_label = "Reinstalling" if installed else "Installing"

            def on_confirm():
                self._set_status(f"{action_label} Ollama...")

                def install_work():
                    try:
                        install_args = ["--reinstall"] if installed else []
                        proc = self._run_ollama_helper("install", *install_args)
                    except FileNotFoundError as exc:
                        self._set_status("Unable to launch the Ollama installer.")
                        self._append_log(f"Installer launch failed: {exc}")
                        Clock.schedule_once(
                            lambda *_: show_fading_alert(
                                "Install Ollama",
                                "Unable to launch the Ollama installer command.",
                                duration=2.0,
                                fade_duration=1.0,
                            ),
                            0,
                        )
                        return

                    output = f"{proc.stdout or ''}\n{proc.stderr or ''}".strip()
                    command_text = "python -m llm.service install"
                    if installed:
                        command_text = f"{command_text} --reinstall"
                    self._append_log(f"$ {command_text}\n{output or f'exit {proc.returncode}'}")

                    if proc.returncode == 0:
                        state = ollama_service.inspect_service_state()
                        if state.get("installed"):
                            self._set_status("Ollama install completed.")
                            self.refresh_ollama_status()
                            self.refresh_local_models()
                            return

                        self._set_status("Ollama installer launched.")
                        Clock.schedule_once(
                            lambda *_: show_fading_alert(
                                "Install Ollama",
                                output
                                or (
                                    "Installer launched. Complete the install, then refresh "
                                    "the Ollama screen or restart BatLLM."
                                ),
                                duration=3.0,
                                fade_duration=1.0,
                            ),
                            0,
                        )
                        return

                    self._set_status("Ollama installer failed to launch.")
                    Clock.schedule_once(
                        lambda *_: show_fading_alert(
                            "Install Ollama",
                            output or "The Ollama install command returned a non-zero exit status.",
                            duration=2.5,
                            fade_duration=1.0,
                        ),
                        0,
                    )

                self._run_in_thread(install_work)

            def on_cancel():
                self._set_status("Install canceled.")
                self._append_log(f"{title} canceled.")

            Clock.schedule_once(
                lambda *_: show_confirmation_dialog(title, message, on_confirm, on_cancel),
                0,
            )

        self._run_in_thread(work)

    def start_ollama(self):
        self._set_status("Starting Ollama...")

        def work():
            warmup_timeout_config = getattr(
                self,
                "_warmup_timeout_config",
                lambda: {"warmup_timeout": config.get("llm", "warmup_timeout")},
            )
            warmup_timeout = ollama_service.resolve_warmup_timeout(warmup_timeout_config())
            proc = self._run_ollama_helper("start", "--warmup-timeout", f"{warmup_timeout:g}")
            combined = f"{proc.stdout}\n{proc.stderr}".strip()
            self._append_log(
                f"$ python -m llm.service start --warmup-timeout {warmup_timeout:g}\n{combined or '(no output)'}"
            )

            if proc.returncode == 0:
                configured_model = str(
                    config.get("llm", "last_served_model") or config.get("llm", "model") or ""
                ).strip()
                self._managed_model_name = configured_model or None
                self._remember_served_model(configured_model)
                self._set_status("Ollama started successfully.")
                self.refresh_ollama_status()
                self.refresh_local_models()
                return

            self._set_status("Failed to start Ollama.")
            msg = combined or "Unknown startup error"
            show_fading_alert("Start Ollama", msg, duration=2.5, fade_duration=1.0)

            msg_lower = msg.lower()
            if (
                "command not found" in msg_lower
                or "ollama: not found" in msg_lower
                or "not recognized as an internal or external command" in msg_lower
            ):
                Clock.schedule_once(lambda *_: self.request_install_ollama(), 0)

        self._run_in_thread(work)

    def stop_ollama(self):
        self._set_status("Stopping Ollama...")

        def work():
            proc = self._run_ollama_helper("stop", "-v")
            combined = f"{proc.stdout}\n{proc.stderr}".strip()
            self._append_log(f"$ python -m llm.service stop -v\n{combined or '(no output)'}")

            if proc.returncode == 0:
                self._managed_model_name = None
                self._set_status("Ollama stopped.")
                self.refresh_ollama_status()
                return

            self._set_status("Stop command returned non-zero exit.")
            show_fading_alert("Stop Ollama", combined or "Unknown stop error",
                              duration=2.0, fade_duration=1.0)

        self._run_in_thread(work)

    def _current_model_entries(self, entries: list[dict[str, str]], model_names: list[str]):
        return entries if entries else [{"name": name, "display": name} for name in model_names]

    def _select_local_model(self, model_name: str):
        self._set_local_selection(model_name)
        self._append_log(f"Selected local model: {model_name}")

    def _select_remote_model(self, model_name: str):
        self._set_remote_selection(model_name)
        self._append_log(f"Selected remote model: {self.selected_remote_model_label}")

    def refresh_all(self):
        self._append_log("Refreshing...")
        self.refresh_ollama_status()
        self.refresh_local_models()
        self.refresh_remote_models()

    def open_local_model_selector(self):
        self._append_log("Refreshing local models...")

        self.refresh_local_models(
            on_complete=lambda: self._show_model_picker(
                title="Local Models",
                entries=self._current_model_entries(self._local_model_entries, self.local_models),
                selected_value=self.selected_local_model,
                on_select=self._select_local_model,
            )
        )

    def open_remote_model_selector(self):
        self._append_log("Refreshing remote models...")

        self.refresh_remote_models(
            on_complete=lambda: self._show_model_picker(
                title="Remote Models",
                entries=self._current_model_entries(self._remote_model_entries, self.remote_models),
                selected_value=self.selected_remote_model,
                on_select=self._select_remote_model,
            )
        )

    def refresh_local_models(self, on_complete=None):
        self._set_status("Refreshing local models...")

        def work():
            try:
                names = [
                    name for name in modelito_ollama_service.list_local_models() if str(name).strip()
                ]

                def update(*_):
                    self._local_model_entries = [{"name": name, "display": name} for name in names]
                    self.local_models = names
                    current = self.selected_local_model.strip() or str(config.get("llm", "model") or "")
                    self._set_local_selection(
                        current if current in names else (names[0] if names else ""))
                    self._set_status(f"Loaded {len(names)} local model(s).")
                    models_text = ", ".join(names) if names else "none"
                    self._append_log(
                        f"modelito list_local_models\nLoaded local models: {models_text}"
                    )
                    self._schedule_ui_callback(on_complete)

                Clock.schedule_once(update, 0)
            except Exception as exc:
                self._set_status(f"Unable to list local models: {exc}")
                self._append_log(f"Local model refresh failed\n{exc}")
                self._schedule_ui_callback(on_complete)

        self._run_in_thread(work)

    def refresh_remote_models(self, on_complete=None):
        self._set_status("Refreshing remote model list...")

        def work():
            try:
                entries: list[dict[str, str]] = []
                for entry in modelito_ollama_service.list_remote_model_catalog():
                    raw = entry.raw if isinstance(entry.raw, dict) else {}
                    size = str(
                        raw.get("parameter_size")
                        or raw.get("size")
                        or raw.get("size_label")
                        or ""
                    ).strip()
                    display = entry.name
                    if size:
                        display = f"{display} ({size})"
                    if entry.installed:
                        display = f"{display} [installed]"
                    entries.append({"name": entry.name, "display": display, "size": size})
                names = [entry["name"] for entry in entries]

                def update(*_):
                    self._remote_model_entries = entries
                    self._remote_model_display_map = {
                        entry["name"]: entry["display"] for entry in entries
                    }
                    self.remote_models = names
                    selected = self.selected_remote_model if self.selected_remote_model in names else (
                        names[0] if names else ""
                    )
                    self._set_remote_selection(selected)
                    self._set_status(f"Loaded {len(names)} remote model(s).")
                    self._append_log(
                        f"modelito list_remote_model_catalog\nLoaded {len(names)} remote models"
                    )
                    self._schedule_ui_callback(on_complete)

                Clock.schedule_once(update, 0)
            except Exception as exc:
                self._set_status(f"Unable to load remote models: {exc}")
                self._append_log(f"Remote model refresh failed\n{exc}")
                self._schedule_ui_callback(on_complete)

        self._run_in_thread(work)

    def _get_running_model_names(self) -> list[str]:
        base_url, port = self._llm_endpoint()
        host = f"{base_url.removeprefix('http://').removeprefix('https://')}:{port}"
        try:
            return modelito_ollama_service.running_model_names(host)
        except Exception:
            return []

    def _preload_model(self, model_name: str):
        base_url, port = self._llm_endpoint()
        request_timeout = ollama_service.resolve_request_timeout(
            self._llm_timeout_config(model_name),
            model=model_name,
        )
        ollama_service.preload_model(
            base_url,
            port,
            model_name,
            timeout=request_timeout,
        )
        payload = {"ok": True, "model": model_name, "timeout": request_timeout}
        self._append_log(f"modelito preload_model\n{json.dumps(payload)}")
        return payload

    def _stop_serving_model(self, model_name: str):
        base_url, port = self._llm_endpoint()
        host = f"{base_url.removeprefix('http://').removeprefix('https://')}:{port}"
        proc = ollama_service.run_ollama_command("stop", model_name, host=host)
        combined = ((proc.stdout or "") + (proc.stderr or "")).strip()
        self._append_log(f"$ ollama stop {model_name}\n{combined or f'exit {proc.returncode}'}")
        if proc.returncode != 0:
            raise RuntimeError(combined or f"Failed to stop model {model_name}")
        return {"ok": True}

    def _ensure_model_serving(self, model_name: str):
        base_url, port = self._llm_endpoint()
        request_timeout = ollama_service.resolve_request_timeout(
            self._llm_timeout_config(model_name),
            model=model_name,
        )
        try:
            result = modelito_ollama_service.ensure_model_ready_detailed(
                model_name,
                host=base_url,
                port=port,
                auto_start=True,
                allow_download=False,
                timeout=request_timeout,
            )
        except Exception as exc:
            self._append_log(f"Model readiness check failed for {model_name}: {exc}")
            raise RuntimeError(str(exc)) from exc
        if not result.success:
            detail = result.error or result.message or f"modelito could not make {model_name} ready"
            raise RuntimeError(detail)
        self._append_log(
            f"modelito ensure_model_ready_detailed\nmodel={model_name} phase={result.phase} elapsed={result.elapsed_seconds:.2f}s source={result.source}"
        )
        return {"ready": True}

    def set_model_from_selection(self):
        model = self.selected_local_model.strip()
        if not model:
            show_fading_alert("Model Selection", "Select a local model first.",
                              duration=1.5, fade_duration=1.0)
            return

        config.set("llm", "model", model)
        config.save()
        self._set_status(f"Loading model: {model}")
        self._append_log(f"Configured BatLLM model: {model}")

        def work():
            try:
                running_before = set(self._get_running_model_names())
                previous_managed = self._managed_model_name

                if previous_managed and previous_managed != model and previous_managed in running_before:
                    self._set_status(f"Stopping previous BatLLM model: {previous_managed}")
                    self._append_log(f"Stopping previous BatLLM model: {previous_managed}")
                    self._stop_serving_model(previous_managed)
                    running_before.discard(previous_managed)

                self._ensure_model_serving(model)
                self._remember_served_model(model)
                if model not in running_before or previous_managed == model:
                    self._managed_model_name = model
                else:
                    self._managed_model_name = None
                self._set_status(f"Model ready: {model}")
                self._append_log(f"Model ready: {model}")
                self.refresh_ollama_status()
                self.refresh_local_models()
            except RuntimeError as exc:
                self._set_status(f"Failed to serve model: {model}")
                self._append_log(f"Failed to serve model {model}: {exc}")
                Clock.schedule_once(
                    lambda *_: show_fading_alert(
                        "Use Selected",
                        str(exc),
                        duration=2.0,
                        fade_duration=1.0,
                    ),
                    0,
                )

        self._run_in_thread(work)

    def save_selected_model_timeout(self):
        model = self.selected_local_model.strip()
        if not model:
            show_fading_alert(
                "Model Timeout",
                "Select a local model first.",
                duration=1.5,
                fade_duration=1.0,
            )
            return

        raw_value = self.selected_local_timeout_text.strip()
        try:
            timeout_seconds = float(raw_value)
        except ValueError:
            show_fading_alert(
                "Model Timeout",
                "Enter a positive timeout in seconds.",
                duration=1.7,
                fade_duration=1.0,
            )
            return

        if timeout_seconds <= 0:
            show_fading_alert(
                "Model Timeout",
                "Enter a positive timeout in seconds.",
                duration=1.7,
                fade_duration=1.0,
            )
            return

        overrides = self._model_timeout_overrides()
        overrides[model] = timeout_seconds
        self._save_model_timeout_overrides(overrides)
        self._refresh_selected_local_timeout()
        self._set_status(f"Saved timeout for {model}.")
        self._append_log(
            f"Saved model timeout override: {model} -> "
            f"{self._format_timeout_seconds(timeout_seconds)}s"
        )

    def save_warmup_timeout(self):
        raw_value = self.warmup_timeout_text.strip()
        try:
            timeout_seconds = float(raw_value)
        except ValueError:
            show_fading_alert(
                "Warmup Timeout",
                "Enter a positive warmup timeout in seconds.",
                duration=1.7,
                fade_duration=1.0,
            )
            return

        if timeout_seconds <= 0:
            show_fading_alert(
                "Warmup Timeout",
                "Enter a positive warmup timeout in seconds.",
                duration=1.7,
                fade_duration=1.0,
            )
            return

        config.set("llm", "warmup_timeout", timeout_seconds)
        config.save()
        self._refresh_warmup_timeout()
        self._set_status("Saved warmup timeout.")
        self._append_log(
            f"Saved warmup timeout override -> {self._format_timeout_seconds(timeout_seconds)}s"
        )

    def reset_warmup_timeout(self):
        config.set("llm", "warmup_timeout", None)
        config.save()
        self._refresh_warmup_timeout()
        self._set_status("Using default warmup timeout.")
        self._append_log("Cleared warmup timeout override.")

    def reset_selected_model_timeout(self):
        model = self.selected_local_model.strip()
        if not model:
            show_fading_alert(
                "Model Timeout",
                "Select a local model first.",
                duration=1.5,
                fade_duration=1.0,
            )
            return

        removed = self._remove_model_timeout_override(model)
        self._refresh_selected_local_timeout()
        if removed:
            self._set_status(f"Using default timeout for {model}.")
            self._append_log(f"Cleared model timeout override: {model}")
        else:
            self._set_status(f"No saved timeout override for {model}.")
            self._append_log(f"No model timeout override to clear: {model}")

    def _pull_model(self, model_name: str):
        for state in modelito_ollama_service.download_model_progress(model_name, timeout=600.0):
            status = state.message or state.phase or state.error or "working"
            self._set_status(f"Pull {model_name}: {status}")
            event = {
                "model": state.model,
                "phase": state.phase,
                "message": state.message,
                "progress": state.progress,
                "error": state.error,
            }
            self._append_log(f"modelito download_model_progress\n{json.dumps(event)}")

    def request_pull_selected_model(self):
        model = self.selected_remote_model.strip()
        if not model:
            show_fading_alert("Pull Model", "Select a remote model first.",
                              duration=1.5, fade_duration=1.0)
            return

        def on_confirm():
            self._set_status(f"Downloading model: {model}")
            self._append_log(f"Confirmed download for model: {model}")

            def work():
                try:
                    self._pull_model(model)
                    self._set_status(f"Model downloaded: {model}")
                    self._append_log(f"Model downloaded: {model}")
                    self.refresh_local_models()
                except Exception as exc:
                    self._set_status(f"Download failed: {exc}")
                    self._append_log(f"Download failed for {model}: {exc}")

            self._run_in_thread(work)

        show_confirmation_dialog(
            "Download Model",
            f"Download model '{model}' now?",
            on_confirm=on_confirm,
            on_cancel=lambda: (self._set_status("Download canceled."),
                               self._append_log(f"Download canceled: {model}")),
        )

    def _delete_model(self, model_name: str):
        deleted = modelito_ollama_service.delete_model(model_name)
        self._append_log(f"modelito delete_model\n{model_name} -> {deleted}")
        if not deleted:
            raise RuntimeError(f"Failed to delete model {model_name}")

    def request_delete_selected_model(self):
        model = self.selected_local_model.strip()
        if not model:
            show_fading_alert("Delete Model", "Select a local model first.",
                              duration=1.5, fade_duration=1.0)
            return

        def on_confirm():
            self._set_status(f"Deleting model: {model}")
            self._append_log(f"Confirmed delete for model: {model}")

            def work():
                try:
                    if model == self._managed_model_name:
                        self._managed_model_name = None
                    self._delete_model(model)
                    if self._remove_model_timeout_override(model):
                        self._append_log(
                            f"Removed model timeout override for deleted model: {model}")
                    self._set_status(f"Model deleted: {model}")
                    self._append_log(f"Model deleted: {model}")
                    self.refresh_local_models()
                except Exception as exc:
                    self._set_status(f"Delete failed: {exc}")
                    self._append_log(f"Delete failed for {model}: {exc}")

            self._run_in_thread(work)

        show_confirmation_dialog(
            "Delete Model",
            f"Delete local model '{model}'? This cannot be undone.",
            on_confirm=on_confirm,
            on_cancel=lambda: (self._set_status("Delete canceled."),
                               self._append_log(f"Delete canceled: {model}")),
        )
