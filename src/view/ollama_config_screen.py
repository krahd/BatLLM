"""Ollama configuration and model-management screen."""

from __future__ import annotations

from datetime import datetime
import json
import re
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import requests
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
REMOTE_LIBRARY_URL = "https://ollama.com/library"
REMOTE_MODEL_CARD_RE = re.compile(
    r'<a href="/library/([^"/:?#]+)"\s+class="group w-full space-y-5">(.*?)</a>',
    re.S,
)
REMOTE_MODEL_SIZE_RE = re.compile(r'<span x-test-size[^>]*>([^<]+)</span>')


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
    selected_remote_model_label = StringProperty("Select remote model")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._local_model_entries: list[dict[str, str]] = []
        self._remote_model_entries: list[dict[str, str]] = []
        self._remote_model_display_map: dict[str, str] = {}
        self._model_picker_popup = None
        self._managed_model_name: str | None = None

    def on_pre_enter(self, *_args):
        Window.unbind(on_key_down=self.handle_window_key_down)
        Window.bind(on_key_down=self.handle_window_key_down)
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

    def _set_local_selection(self, model_name: str):
        model_name = model_name.strip()
        self.selected_local_model = model_name
        self.selected_local_model_label = model_name or "Select local model"

    def _set_remote_selection(self, model_name: str):
        model_name = model_name.strip()
        self.selected_remote_model = model_name
        self.selected_remote_model_label = (
            self._remote_model_display_map.get(model_name, model_name) or "Select remote model"
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
            button.bind(size=lambda inst, *_: setattr(inst, "text_size", (inst.width - dp(16), None)))
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
        helper = ROOT / "src" / "ollama_service.py"
        return subprocess.run(
            [sys.executable, str(helper), action, *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def _run_ollama_command(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["ollama", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def _collect_ollama_status(self) -> dict[str, Any]:
        base_url, port = self._llm_endpoint()
        configured_model = str(config.get("llm", "model") or "")
        snapshot: dict[str, Any] = {
            "found": False,
            "version": "",
            "running": False,
            "server_version": "",
            "running_models": [],
            "configured_model": configured_model,
            "endpoint": f"{base_url}:{port}",
        }

        try:
            version_proc = self._run_ollama_command("--version")
        except FileNotFoundError:
            self._append_log("$ ollama --version\nollama not found")
            return snapshot

        version_output = (version_proc.stdout or version_proc.stderr).strip()
        snapshot["found"] = version_proc.returncode == 0 or bool(version_output)
        snapshot["version"] = version_output or "unknown"
        self._append_log(
            f"$ ollama --version\n{version_output or f'exit {version_proc.returncode}'}")

        version_url = f"{base_url}:{port}/api/version"
        try:
            version_payload = self._json_get(version_url, timeout=5)
            snapshot["running"] = True
            if isinstance(version_payload, dict):
                snapshot["server_version"] = str(version_payload.get("version", ""))
            self._append_log(f"GET {version_url}\n{json.dumps(version_payload)}")

            ps_url = f"{base_url}:{port}/api/ps"
            ps_payload = self._json_get(ps_url, timeout=5)
            self._append_log(f"GET {ps_url}\n{json.dumps(ps_payload)}")
            if isinstance(ps_payload, dict):
                models = ps_payload.get("models", [])
                snapshot["running_models"] = [
                    model.get("name", "")
                    for model in models
                    if isinstance(model, dict) and model.get("name")
                ]
        except (URLError, HTTPError, ValueError) as exc:
            self._append_log(f"GET {version_url}\n{exc}")

        return snapshot

    def _format_status_report(self, snapshot: dict[str, Any]) -> str:
        lines = []
        configured_model = snapshot.get("configured_model") or "not set"

        if not snapshot.get("found"):
            lines.append("Ollama CLI: not found")
            lines.append("Installed version: unavailable")
            lines.append("Server status: not running")
            lines.append(f"BatLLM model: {configured_model}")
            return "\n".join(lines)

        lines.append("Ollama CLI: found")
        lines.append(f"Installed version: {snapshot.get('version') or 'unknown'}")

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

    def _open_install_guidance(self):
        if sys.platform.startswith("win"):
            suggestion = "Install Ollama for Windows from https://ollama.com/download/windows"
        elif sys.platform == "darwin":
            suggestion = "Install Ollama for macOS from https://ollama.com/download"
        else:
            suggestion = "Install Ollama for Linux from https://ollama.com/download/linux"

        def on_path(path: str):
            cmd = f"Install suggestion: {suggestion}\nProvided path: {path}"
            self._append_log(cmd)
            show_fading_alert("Ollama Install Guidance", cmd, duration=2.5, fade_duration=1.0)

        show_text_input_dialog(
            on_confirm=on_path,
            title="Ollama Not Found",
            message="Ollama was not found. Provide an installer or binary path.",
            input_hint="/path/to/ollama or installer",
        )

    def start_ollama(self):
        self._set_status("Starting Ollama...")

        def work():
            proc = self._run_ollama_helper("start")
            combined = f"{proc.stdout}\n{proc.stderr}".strip()
            self._append_log(f"$ python src/ollama_service.py start\n{combined or '(no output)'}")

            if proc.returncode == 0:
                configured_model = str(config.get("llm", "model") or "").strip()
                self._managed_model_name = configured_model or None
                self._set_status("Ollama started successfully.")
                self.refresh_ollama_status()
                self.refresh_local_models()
                return

            self._set_status("Failed to start Ollama.")
            msg = combined or "Unknown startup error"
            show_fading_alert("Start Ollama", msg, duration=2.5, fade_duration=1.0)

            if "command not found" in msg.lower() or "ollama" in msg.lower():
                Clock.schedule_once(lambda *_: self._open_install_guidance(), 0)

        self._run_in_thread(work)

    def stop_ollama(self):
        self._set_status("Stopping Ollama...")

        def work():
            proc = self._run_ollama_helper("stop", "-v")
            combined = f"{proc.stdout}\n{proc.stderr}".strip()
            self._append_log(f"$ python src/ollama_service.py stop -v\n{combined or '(no output)'}")

            if proc.returncode == 0:
                self._managed_model_name = None
                self._set_status("Ollama stopped.")
                self.refresh_ollama_status()
                return

            self._set_status("Stop command returned non-zero exit.")
            show_fading_alert("Stop Ollama", combined or "Unknown stop error",
                              duration=2.0, fade_duration=1.0)

        self._run_in_thread(work)

    def _json_get(self, url: str, timeout: float = 10.0) -> dict[str, Any]:
        with urlopen(url, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}

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
            base_url, port = self._llm_endpoint()
            tags_url = f"{base_url}:{port}/api/tags"
            try:
                payload = self._json_get(tags_url, timeout=8)
                models = payload.get("models", []) if isinstance(payload, dict) else []
                names = [m.get("name", "") for m in models if isinstance(m, dict) and m.get("name")]

                def update(*_):
                    self._local_model_entries = [{"name": name, "display": name} for name in names]
                    self.local_models = names
                    current = self.selected_local_model.strip() or str(config.get("llm", "model") or "")
                    self._set_local_selection(current if current in names else (names[0] if names else ""))
                    self._set_status(f"Loaded {len(names)} local model(s).")
                    models_text = ", ".join(names) if names else "none"
                    self._append_log(f"GET {tags_url}\nLoaded local models: {models_text}")
                    self._schedule_ui_callback(on_complete)

                Clock.schedule_once(update, 0)
            except (URLError, HTTPError, ValueError) as exc:
                self._set_status(f"Unable to list local models: {exc}")
                self._append_log(f"GET {tags_url}\n{exc}")
                self._schedule_ui_callback(on_complete)

        self._run_in_thread(work)

    def _parse_remote_models_html(self, html: str) -> list[dict[str, str]]:
        seen = set()
        entries: list[dict[str, str]] = []

        for name, block in REMOTE_MODEL_CARD_RE.findall(html):
            name = name.strip()
            if not name or name in seen:
                continue
            seen.add(name)
            size_match = REMOTE_MODEL_SIZE_RE.search(block)
            size = size_match.group(1).strip() if size_match else ""
            display = f"{name} ({size})" if size else name
            entries.append({"name": name, "display": display, "size": size})

        return entries

    def refresh_remote_models(self, on_complete=None):
        self._set_status("Refreshing remote model list...")

        def work():
            try:
                resp = requests.get(REMOTE_LIBRARY_URL, timeout=12)
                resp.raise_for_status()
                entries = self._parse_remote_models_html(resp.text)
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
                        f"GET {REMOTE_LIBRARY_URL}\nLoaded {len(names)} remote models"
                    )
                    self._schedule_ui_callback(on_complete)

                Clock.schedule_once(update, 0)
            except requests.RequestException as exc:
                self._set_status(f"Unable to load remote models: {exc}")
                self._append_log(f"GET {REMOTE_LIBRARY_URL}\n{exc}")
                self._schedule_ui_callback(on_complete)

        self._run_in_thread(work)

    def _get_running_model_names(self) -> list[str]:
        base_url, port = self._llm_endpoint()
        ps_url = f"{base_url}:{port}/api/ps"
        try:
            payload = self._json_get(ps_url, timeout=5)
        except (URLError, HTTPError, ValueError):
            return []

        models = payload.get("models", []) if isinstance(payload, dict) else []
        return [
            model.get("name", "")
            for model in models
            if isinstance(model, dict) and model.get("name")
        ]

    def _preload_model(self, model_name: str):
        base_url, port = self._llm_endpoint()
        url = f"{base_url}:{port}/api/generate"
        resp = requests.post(
            url,
            json={"model": model_name, "keep_alive": "30m"},
            timeout=60,
        )
        resp.raise_for_status()
        payload = resp.json() if resp.content else {}
        self._append_log(f"POST {url}\n{json.dumps(payload)}")
        return payload

    def _stop_serving_model(self, model_name: str):
        base_url, port = self._llm_endpoint()
        url = f"{base_url}:{port}/api/generate"
        resp = requests.post(
            url,
            json={"model": model_name, "keep_alive": 0},
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json() if resp.content else {}
        self._append_log(f"POST {url}\n{json.dumps(payload)}")
        return payload

    def _ensure_model_serving(self, model_name: str):
        try:
            return self._preload_model(model_name)
        except requests.RequestException as exc:
            self._append_log(f"Preload failed for {model_name}: {exc}")
            proc = self._run_ollama_helper("start")
            combined = f"{proc.stdout}\n{proc.stderr}".strip()
            self._append_log(f"$ python src/ollama_service.py start\n{combined or '(no output)'}")
            if proc.returncode != 0:
                raise RuntimeError(
                    combined or f"ollama_service.py start exited {proc.returncode}"
                ) from exc
            return {"started_via_script": True}

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

    def _pull_model(self, model_name: str):
        base_url, port = self._llm_endpoint()
        url = f"{base_url}:{port}/api/pull"

        with requests.post(url, json={"name": model_name}, timeout=30, stream=True) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                try:
                    event = json.loads(line.decode("utf-8"))
                    status = event.get("status") or event.get("error") or "working"
                    self._set_status(f"Pull {model_name}: {status}")
                    self._append_log(f"POST {url}\n{json.dumps(event)}")
                except ValueError:
                    continue

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
                except requests.RequestException as exc:
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
        base_url, port = self._llm_endpoint()
        url = f"{base_url}:{port}/api/delete"
        resp = requests.delete(url, json={"name": model_name}, timeout=10)
        resp.raise_for_status()
        self._append_log(f"DELETE {url}\nDeleted model request: {model_name}")

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
                    self._set_status(f"Model deleted: {model}")
                    self._append_log(f"Model deleted: {model}")
                    self.refresh_local_models()
                except requests.RequestException as exc:
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
