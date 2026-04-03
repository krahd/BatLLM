from __future__ import annotations

import json
import subprocess
import threading
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import requests
from kivy.clock import Clock
from kivy.properties import ListProperty, StringProperty
from kivy.uix.screenmanager import Screen

from configs.app_config import config
from util.utils import show_confirmation_dialog, show_fading_alert, show_text_input_dialog


ROOT = Path(__file__).resolve().parents[2]


class OllamaConfigScreen(Screen):
    status_text = StringProperty("Idle")
    local_models = ListProperty([])
    remote_models = ListProperty([])
    selected_local_model = StringProperty("")
    selected_remote_model = StringProperty("")

    def on_pre_enter(self, *_args):
        self.refresh_local_models()

    def go_to_settings_screen(self):
        self.manager.current = "settings"

    def _llm_endpoint(self) -> tuple[str, int]:
        url = str(config.get("llm", "url") or "http://localhost").rstrip("/")
        port = int(config.get("llm", "port") or 11434)
        return url, port

    def _chat_path(self) -> str:
        return str(config.get("llm", "path") or "/api/chat")

    def _set_status(self, text: str):
        Clock.schedule_once(lambda *_: setattr(self, "status_text", text), 0)

    def _run_in_thread(self, fn):
        threading.Thread(target=fn, daemon=True).start()

    def _run_script(self, script_name: str, *args: str) -> subprocess.CompletedProcess:
        script = ROOT / script_name
        return subprocess.run(
            [str(script), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def _open_install_guidance(self):
        def on_path(path: str):
            cmd = f"Install suggestion: brew install ollama\nProvided path: {path}"
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
            proc = self._run_script("start_ollama.sh")
            combined = f"{proc.stdout}\n{proc.stderr}".strip()

            if proc.returncode == 0:
                self._set_status("Ollama started successfully.")
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
            proc = self._run_script("stop_ollama.sh", "-v")
            combined = f"{proc.stdout}\n{proc.stderr}".strip()

            if proc.returncode == 0:
                self._set_status("Ollama stopped.")
                return

            self._set_status("Stop command returned non-zero exit.")
            show_fading_alert("Stop Ollama", combined or "Unknown stop error",
                              duration=2.0, fade_duration=1.0)

        self._run_in_thread(work)

    def _json_get(self, url: str, timeout: float = 10.0) -> dict[str, Any]:
        with urlopen(url, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}

    def refresh_local_models(self):
        self._set_status("Refreshing local models...")

        def work():
            base_url, port = self._llm_endpoint()
            tags_url = f"{base_url}:{port}/api/tags"
            try:
                payload = self._json_get(tags_url, timeout=8)
                models = payload.get("models", []) if isinstance(payload, dict) else []
                names = [m.get("name", "") for m in models if isinstance(m, dict) and m.get("name")]

                def update(*_):
                    self.local_models = names
                    current = str(config.get("llm", "model") or "")
                    self.selected_local_model = current if current in names else (
                        names[0] if names else "")
                    self._set_status(f"Loaded {len(names)} local model(s).")

                Clock.schedule_once(update, 0)
            except (URLError, HTTPError, ValueError) as exc:
                self._set_status(f"Unable to list local models: {exc}")

        self._run_in_thread(work)

    def refresh_remote_models(self):
        self._set_status("Refreshing remote model list...")

        def work():
            try:
                resp = requests.get("https://ollamadb.dev/api/v1/models", timeout=12)
                resp.raise_for_status()
                data = resp.json()
                rows = data.get("data", []) if isinstance(data, dict) else []
                names = []
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    name = row.get("name") or row.get("model") or row.get("slug")
                    if name:
                        names.append(str(name))

                names = sorted(set(names))

                def update(*_):
                    self.remote_models = names
                    self.selected_remote_model = names[0] if names else ""
                    self._set_status(f"Loaded {len(names)} remote model(s).")

                Clock.schedule_once(update, 0)
            except requests.RequestException as exc:
                self._set_status(f"Unable to load remote models: {exc}")

        self._run_in_thread(work)

    def set_model_from_selection(self):
        model = self.selected_local_model.strip()
        if not model:
            show_fading_alert("Model Selection", "Select a local model first.",
                              duration=1.5, fade_duration=1.0)
            return

        config.set("llm", "model", model)
        config.save()
        self._set_status(f"Selected model saved: {model}")

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

            def work():
                try:
                    self._pull_model(model)
                    self._set_status(f"Model downloaded: {model}")
                    self.refresh_local_models()
                except requests.RequestException as exc:
                    self._set_status(f"Download failed: {exc}")

            self._run_in_thread(work)

        show_confirmation_dialog(
            "Download Model",
            f"Download model '{model}' now?",
            on_confirm=on_confirm,
            on_cancel=lambda: self._set_status("Download canceled."),
        )

    def _delete_model(self, model_name: str):
        base_url, port = self._llm_endpoint()
        url = f"{base_url}:{port}/api/delete"
        resp = requests.delete(url, json={"name": model_name}, timeout=10)
        resp.raise_for_status()

    def request_delete_selected_model(self):
        model = self.selected_local_model.strip()
        if not model:
            show_fading_alert("Delete Model", "Select a local model first.",
                              duration=1.5, fade_duration=1.0)
            return

        def on_confirm():
            self._set_status(f"Deleting model: {model}")

            def work():
                try:
                    self._delete_model(model)
                    self._set_status(f"Model deleted: {model}")
                    self.refresh_local_models()
                except requests.RequestException as exc:
                    self._set_status(f"Delete failed: {exc}")

            self._run_in_thread(work)

        show_confirmation_dialog(
            "Delete Model",
            f"Delete local model '{model}'? This cannot be undone.",
            on_confirm=on_confirm,
            on_cancel=lambda: self._set_status("Delete canceled."),
        )
