from __future__ import annotations

from datetime import datetime
import json
import subprocess
import threading
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import requests
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import ListProperty, StringProperty
from kivy.uix.screenmanager import Screen

from configs.app_config import config
from util.utils import (
    show_confirmation_dialog,
    show_fading_alert,
    show_text_input_dialog,
    switch_screen,
)


ROOT = Path(__file__).resolve().parents[2]


class OllamaConfigScreen(Screen):
    status_text = StringProperty("Idle")
    status_details = StringProperty("Ollama status has not been checked yet.")
    output_log = StringProperty("")
    local_models = ListProperty([])
    remote_models = ListProperty([])
    selected_local_model = StringProperty("")
    selected_remote_model = StringProperty("")

    def on_pre_enter(self, *_args):
        Window.unbind(on_key_down=self.handle_window_key_down)
        Window.bind(on_key_down=self.handle_window_key_down)
        self.refresh_ollama_status()
        self.refresh_local_models()

    def on_pre_leave(self, *_args):
        Window.unbind(on_key_down=self.handle_window_key_down)

    def handle_window_key_down(self, _window, key, *_args):
        if key != 27:
            return False

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

    def _run_script(self, script_name: str, *args: str) -> subprocess.CompletedProcess:
        script = ROOT / script_name
        return subprocess.run(
            [str(script), *args],
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
        def on_path(path: str):
            cmd = f"Install suggestion: brew install ollama\nProvided path: {path}"
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
            proc = self._run_script("start_ollama.sh")
            combined = f"{proc.stdout}\n{proc.stderr}".strip()
            self._append_log(f"$ ./start_ollama.sh\n{combined or '(no output)'}")

            if proc.returncode == 0:
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
            proc = self._run_script("stop_ollama.sh", "-v")
            combined = f"{proc.stdout}\n{proc.stderr}".strip()
            self._append_log(f"$ ./stop_ollama.sh -v\n{combined or '(no output)'}")

            if proc.returncode == 0:
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
                    models_text = ", ".join(names) if names else "none"
                    self._append_log(f"GET {tags_url}\nLoaded local models: {models_text}")

                Clock.schedule_once(update, 0)
            except (URLError, HTTPError, ValueError) as exc:
                self._set_status(f"Unable to list local models: {exc}")
                self._append_log(f"GET {tags_url}\n{exc}")

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
                    self._append_log(
                        f"GET https://ollamadb.dev/api/v1/models\nLoaded {len(names)} remote models"
                    )

                Clock.schedule_once(update, 0)
            except requests.RequestException as exc:
                self._set_status(f"Unable to load remote models: {exc}")
                self._append_log(f"GET https://ollamadb.dev/api/v1/models\n{exc}")

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
        self._append_log(f"Configured BatLLM model: {model}")
        self.refresh_ollama_status()

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
