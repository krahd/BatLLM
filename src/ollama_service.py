"""Cross-platform Ollama lifecycle helper for BatLLM."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import shlex
import subprocess
import sys
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import psutil
import yaml


MIN_PYTHON = (3, 10)
ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "src" / "configs" / "config.yaml"
REMOTE_TIMEOUT_CATALOG_PATH = ROOT / "src" / "assets" / "ollama_remote_timeout_catalog.json"
UNIX_INSTALL_URL = "https://ollama.com/install.sh"
WINDOWS_INSTALL_URL = "https://ollama.com/install.ps1"
COMMON_MODEL_TIMEOUTS = {
    "mistral-small": 60.0,
    "mistral-small:latest": 60.0,
    "smollm2": 35.0,
    "smollm2:latest": 35.0,
    "llama3.2": 75.0,
    "llama3.2:latest": 75.0,
    "phi3": 90.0,
    "phi3:14b": 90.0,
    "qwen3:30b": 120.0,
}


def require_supported_python() -> None:
    """Exit early with a clear message on unsupported Python versions."""
    if sys.version_info >= MIN_PYTHON:
        return
    version = ".".join(str(part) for part in sys.version_info[:3])
    raise SystemExit(f"BatLLM requires Python 3.10 or newer. Detected Python {version}.")


def load_llm_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Load the LLM configuration required to manage the local Ollama service."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    llm = data.get("llm") or {}
    model_timeouts = llm.get("model_timeouts")
    if not isinstance(model_timeouts, dict):
        model_timeouts = {}
    return {
        "last_served_model": str(llm.get("last_served_model") or "").strip(),
        "model": str(llm.get("model") or "").strip(),
        "model_timeouts": dict(model_timeouts),
        "timeout": llm.get("timeout"),
        "url": str(llm.get("url") or "http://localhost").strip().rstrip("/"),
        "port": int(llm.get("port") or 11434),
    }


def _parse_positive_timeout(raw_timeout: Any) -> float | None:
    """Parse a timeout value and return it only when it is positive."""
    try:
        timeout = float(raw_timeout)
    except (TypeError, ValueError):
        return None
    return timeout if timeout > 0 else None


def common_model_timeout(model_name: str) -> float | None:
    """Return a built-in timeout default for common BatLLM models."""
    normalized = str(model_name or "").strip()
    if not normalized:
        return None
    if normalized in COMMON_MODEL_TIMEOUTS:
        return COMMON_MODEL_TIMEOUTS[normalized]
    family = normalized.split(":", 1)[0]
    return COMMON_MODEL_TIMEOUTS.get(family)


def load_remote_timeout_catalog(path: Path = REMOTE_TIMEOUT_CATALOG_PATH) -> dict[str, Any]:
    """Load the shipped remote-model timeout catalog."""
    if not path.exists():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}

    return data if isinstance(data, dict) else {}


def _parse_model_scale_billions(size_label: str) -> float | None:
    """Convert a remote-model size label such as ``7b`` or ``8x7b`` into billions."""
    normalized = str(size_label or "").strip().lower().replace(" ", "")
    if not normalized:
        return None

    multiplicative = re.fullmatch(r"([0-9.]+)x([0-9.]+)([bmk])", normalized)
    if multiplicative:
        factor = float(multiplicative.group(1))
        value = float(multiplicative.group(2))
        suffix = multiplicative.group(3)
        scale = value * factor
    else:
        simple = re.search(r"([0-9.]+)([bmk])", normalized)
        if simple is None:
            return None
        scale = float(simple.group(1))
        suffix = simple.group(2)

    if suffix == "b":
        return scale
    if suffix == "m":
        return scale / 1000.0
    if suffix == "k":
        return scale / 1_000_000.0
    return None


def estimate_remote_model_timeout_details(
    model_name: str,
    *,
    size_label: str = "",
    default: float | None = None,
) -> tuple[float, str]:
    """Estimate a timeout for a remote Ollama library entry using the shipped catalog."""
    catalog = load_remote_timeout_catalog()
    fallback = float(catalog.get("default_timeout") or default or 120.0)
    normalized_name = str(model_name or "").strip().lower()

    for rule in catalog.get("family_overrides", []):
        pattern = str(rule.get("pattern") or "")
        if pattern and re.search(pattern, normalized_name, re.IGNORECASE):
            timeout = _parse_positive_timeout(rule.get("timeout"))
            if timeout is not None:
                return timeout, str(rule.get("source") or "the remote family catalog")

    size_billions = _parse_model_scale_billions(size_label)
    timeout = fallback
    source = "the remote timeout catalog fallback"

    if size_billions is not None:
        for band in catalog.get("size_bands", []):
            max_billions = band.get("max_billions")
            band_timeout = _parse_positive_timeout(band.get("timeout"))
            try:
                band_limit = float(max_billions)
            except (TypeError, ValueError):
                continue
            if band_timeout is None:
                continue
            if size_billions <= band_limit:
                timeout = band_timeout
                source = str(
                    band.get("source")
                    or f"the {band_limit:g}B remote size band"
                )
                break

    for rule in catalog.get("keyword_adjustments", []):
        pattern = str(rule.get("pattern") or "")
        if not pattern or not re.search(pattern, normalized_name, re.IGNORECASE):
            continue

        try:
            offset = float(rule.get("offset") or 0.0)
        except (TypeError, ValueError):
            offset = 0.0

        minimum = _parse_positive_timeout(rule.get("minimum"))
        timeout = timeout + offset
        if minimum is not None:
            timeout = max(timeout, minimum)
        timeout = max(20.0, timeout)
        source = str(rule.get("source") or source)

    return timeout, source


def resolve_request_timeout_details(
    llm: Mapping[str, Any],
    default: float = 120.0,
    *,
    model: str | None = None,
) -> tuple[float, str]:
    """Resolve the effective timeout and identify the source of that value."""
    model_name = str(model or llm.get("model") or "").strip()
    model_timeouts = llm.get("model_timeouts")
    if isinstance(model_timeouts, dict) and model_name:
        model_timeout = _parse_positive_timeout(model_timeouts.get(model_name))
        if model_timeout is not None:
            return model_timeout, "model_override"

    configured_timeout = _parse_positive_timeout(llm.get("timeout"))
    if configured_timeout is not None:
        return configured_timeout, "global_override"

    model_default = common_model_timeout(model_name)
    if model_default is not None:
        return model_default, "model_default"

    return default, "fallback_default"


def resolve_request_timeout(
    llm: Mapping[str, Any],
    default: float = 120.0,
    *,
    model: str | None = None,
) -> float:
    """Resolve the effective Ollama request timeout for the selected model."""
    timeout, _source = resolve_request_timeout_details(llm, default=default, model=model)
    return timeout


def preferred_start_model(llm: Mapping[str, Any]) -> str:
    """Prefer the last BatLLM-served model, then fall back to the configured model."""
    last_served_model = str(llm.get("last_served_model") or "").strip()
    model = str(llm.get("model") or "").strip()
    return last_served_model or model


def save_last_served_model(model: str, path: Path = CONFIG_PATH) -> None:
    """Persist the most recent BatLLM-managed Ollama model."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    llm = data.setdefault("llm", {})
    llm["last_served_model"] = model.strip()
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def ollama_binary_candidates() -> list[Path]:
    """Return CLI locations to probe when PATH lookup is not enough."""
    candidates: list[Path] = []

    discovered = shutil.which("ollama")
    if discovered:
        candidates.append(Path(discovered))

    if os.name == "nt":
        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            candidates.append(Path(local_appdata) / "Programs" / "Ollama" / "ollama.exe")
        candidates.append(Path.home() / "AppData" / "Local" / "Programs" / "Ollama" / "ollama.exe")
    elif sys.platform == "darwin":
        candidates.extend(
            [
                Path("/Applications/Ollama.app/Contents/Resources/ollama"),
                Path("/Applications/Ollama.app/Contents/MacOS/Ollama"),
                Path("/usr/local/bin/ollama"),
                Path("/opt/homebrew/bin/ollama"),
            ]
        )
    else:
        candidates.extend(
            [
                Path("/usr/local/bin/ollama"),
                Path("/usr/bin/ollama"),
                Path("/bin/ollama"),
            ]
        )

    unique: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        unique.append(candidate)
    return unique


def resolve_ollama_command() -> str:
    """Resolve the best available Ollama CLI path for the current platform."""
    for candidate in ollama_binary_candidates():
        if candidate.exists():
            return str(candidate)
    raise FileNotFoundError("ollama")


def ollama_installed() -> bool:
    """Return ``True`` when an Ollama CLI installation can be resolved."""
    try:
        resolve_ollama_command()
    except FileNotFoundError:
        return False
    return True


def ollama_version_text(host: str | None = None) -> str:
    """Return the current Ollama CLI version output, if available."""
    try:
        proc = run_ollama_command("--version", host=host)
    except FileNotFoundError:
        return ""
    return (proc.stdout or proc.stderr).strip()


def install_command_for_current_platform(platform_name: str | None = None) -> tuple[list[str], str]:
    """Return the official Ollama install command and its display form."""
    platform_name = platform_name or sys.platform

    if platform_name.startswith("win"):
        command = [
            "powershell.exe",
            "-NoExit",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            f"irm {WINDOWS_INSTALL_URL} | iex",
        ]
        return command, f"irm {WINDOWS_INSTALL_URL} | iex"

    install_command = f"export OLLAMA_NO_START=1; curl -fsSL {shlex.quote(UNIX_INSTALL_URL)} | sh"
    return ["/bin/sh", "-lc", install_command], install_command


def _linux_terminal_launcher() -> list[str] | None:
    """Return a terminal emulator suitable for interactive Linux installs."""
    launchers = [
        ["x-terminal-emulator", "-e"],
        ["gnome-terminal", "--"],
        ["konsole", "-e"],
        ["xterm", "-e"],
    ]
    for launcher in launchers:
        if shutil.which(launcher[0]):
            return launcher
    return None


def install_service(reinstall: bool = False) -> tuple[int, str]:
    """Launch the official Ollama installer for the current platform."""
    action = "reinstall" if reinstall else "install"
    command, display = install_command_for_current_platform()

    try:
        if os.name == "nt":
            subprocess.Popen(command, cwd=ROOT, creationflags=subprocess.CREATE_NEW_CONSOLE)
            return 0, f"Launched the official Ollama {action} workflow in PowerShell."

        if sys.platform == "darwin":
            script_literal = display.replace("\\", "\\\\").replace('"', '\\"')
            proc = subprocess.run(
                [
                    "osascript",
                    "-e",
                    f'tell application "Terminal" to do script "{script_literal}"',
                    "-e",
                    'tell application "Terminal" to activate',
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            if proc.returncode != 0:
                details = (proc.stderr or proc.stdout or "Unable to open Terminal.").strip()
                return proc.returncode, details
            return 0, f"Launched the official Ollama {action} workflow in Terminal."

        terminal = _linux_terminal_launcher()
        if terminal is not None:
            subprocess.Popen([*terminal, *command], cwd=ROOT)
            return 0, f"Launched the official Ollama {action} workflow in a terminal window."

        proc = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        combined = ((proc.stdout or "") + (proc.stderr or "")).strip()
        if proc.returncode == 0:
            return 0, combined or f"Completed the official Ollama {action} workflow."
        return proc.returncode, combined or f"Ollama {action} failed."
    except FileNotFoundError as exc:
        return 1, f"Unable to launch the Ollama installer command ({display}): {exc}"


def endpoint_url(url: str, port: int, path: str) -> str:
    """Build a full URL for the configured Ollama endpoint."""
    return f"{url}:{port}{path}"


def json_get(url: str, timeout: float = 5.0) -> dict:
    """Read JSON from an HTTP GET endpoint."""
    with urlopen(url, timeout=timeout) as response:
        body = response.read().decode("utf-8")
    return json.loads(body) if body else {}


def json_post(url: str, payload: dict, timeout: float = 60.0) -> dict:
    """Send JSON to an HTTP POST endpoint and decode the JSON response."""
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8")
    return json.loads(body) if body else {}


def server_is_up(url: str, port: int) -> bool:
    """Return ``True`` when the Ollama HTTP API responds on the configured port."""
    try:
        json_get(endpoint_url(url, port, "/api/version"), timeout=2.0)
        return True
    except (URLError, HTTPError, ValueError):
        return False


def inspect_service_state(config_path: Path = CONFIG_PATH) -> dict[str, object]:
    """Return the install/runtime state BatLLM cares about at startup."""
    llm = load_llm_config(config_path)
    url = str(llm["url"])
    port = int(llm["port"])
    host = f"{url.removeprefix('http://').removeprefix('https://')}:{port}"
    return {
        "installed": ollama_installed(),
        "version": ollama_version_text(host=host),
        "running": server_is_up(url, port),
        "configured_model": str(llm["model"]),
        "last_served_model": str(llm["last_served_model"]),
        "startup_model": preferred_start_model(llm),
        "url": url,
        "port": port,
    }


def run_ollama_command(*args: str, host: str | None = None) -> subprocess.CompletedProcess:
    """Run an Ollama CLI command and capture the result."""
    env = os.environ.copy()
    if host:
        env["OLLAMA_HOST"] = host
    command = resolve_ollama_command()
    return subprocess.run(
        [command, *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def start_detached_ollama_serve(host: str) -> subprocess.Popen:
    """Start ``ollama serve`` in the background for the current platform."""
    command = resolve_ollama_command()
    kwargs: dict[str, object] = {
        "cwd": ROOT,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "stdin": subprocess.DEVNULL,
        "env": {**os.environ, "OLLAMA_HOST": host},
        "text": True,
    }

    if os.name == "nt":
        kwargs["creationflags"] = (
            subprocess.DETACHED_PROCESS
            | subprocess.CREATE_NEW_PROCESS_GROUP
            | subprocess.CREATE_NO_WINDOW
        )
    else:
        kwargs["start_new_session"] = True

    return subprocess.Popen([command, "serve"], **kwargs)


def wait_until_ready(url: str, port: int, timeout_seconds: float = 60.0) -> None:
    """Wait until the Ollama HTTP API becomes reachable."""
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if server_is_up(url, port):
            return
        time.sleep(1)
    raise RuntimeError(f"ollama serve did not become ready at {url}:{port}/api/version")


def preload_model(url: str, port: int, model: str, timeout: float = 120.0) -> None:
    """Warm the selected model through the local Ollama API."""
    json_post(
        endpoint_url(url, port, "/api/generate"),
        {"model": model, "keep_alive": "30m"},
        timeout=timeout,
    )


def start_service(config_path: Path = CONFIG_PATH) -> int:
    """Start Ollama if needed, ensure the configured model is present, and warm it."""
    llm = load_llm_config(config_path)
    model = preferred_start_model(llm)
    timeout = resolve_request_timeout(llm, model=model)
    url = str(llm["url"])
    port = int(llm["port"])
    host = f"{url.removeprefix('http://').removeprefix('https://')}:{port}"

    if not model:
        print(f"No model configured in {config_path}", file=sys.stderr)
        return 1

    try:
        version_proc = run_ollama_command("--version", host=host)
    except FileNotFoundError:
        print("ollama: command not found", file=sys.stderr)
        return 1

    if version_proc.returncode != 0 and not (version_proc.stdout or version_proc.stderr):
        print("ollama CLI failed to start", file=sys.stderr)
        return 1

    started = False
    if server_is_up(url, port):
        print(f"Ollama already serving at {host}")
    else:
        print(f"Starting ollama serve at {host} ...")
        start_detached_ollama_serve(host)
        wait_until_ready(url, port)
        started = True
        print(f"Ollama is ready at {host}")

    pull_proc = run_ollama_command("pull", model, host=host)
    if pull_proc.returncode != 0:
        sys.stderr.write((pull_proc.stdout or "") + (pull_proc.stderr or ""))
        return pull_proc.returncode

    preload_model(url, port, model, timeout=timeout)
    save_last_served_model(model, config_path)

    if started:
        print(f"Completed: started ollama at {host}, pulled and warmed model '{model}'.")
    else:
        print(f"Completed: ollama already running at {host}; pulled and warmed model '{model}'.")
    return 0


def running_model_names(host: str) -> list[str]:
    """Return the names reported by ``ollama ps``."""
    proc = run_ollama_command("ps", host=host)
    if proc.returncode != 0:
        return []

    names: list[str] = []
    for line in (proc.stdout or "").splitlines()[1:]:
        line = line.strip()
        if not line:
            continue
        names.append(line.split()[0])
    return names


def _listener_pids_from_connections(connections, port: int) -> list[int]:
    """Extract listener process IDs for the configured TCP port."""
    pids: set[int] = set()
    for conn in connections:
        if conn.status != psutil.CONN_LISTEN or not conn.laddr:
            continue
        if conn.laddr.port != port or conn.pid is None:
            continue
        pids.add(conn.pid)
    return sorted(pids)


def find_ollama_listener_pids(port: int) -> list[int]:
    """Return process IDs listening on the configured TCP port.

    On macOS, ``psutil.net_connections(kind="inet")`` may raise ``AccessDenied``
    while scanning unrelated processes. Fall back to inspecting only processes with
    ``ollama`` in the name so BatLLM can still stop the local server it started.
    """
    try:
        return _listener_pids_from_connections(psutil.net_connections(kind="inet"), port)
    except psutil.AccessDenied:
        pass

    pids: set[int] = set()
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            name = str((proc.info or {}).get("name") or proc.name()).lower()
        except psutil.Error:
            continue
        if "ollama" not in name:
            continue
        try:
            connections = proc.net_connections(kind="inet")
        except psutil.Error:
            continue
        for conn in connections:
            if conn.status != psutil.CONN_LISTEN or not conn.laddr:
                continue
            if conn.laddr.port != port:
                continue
            pids.add(getattr(conn, "pid", None) or proc.pid)
    return sorted(pids)


def stop_service(config_path: Path = CONFIG_PATH, verbose: bool = False) -> int:
    """Stop models reported by Ollama and terminate the listening server process."""
    llm = load_llm_config(config_path)
    url = str(llm["url"])
    port = int(llm["port"])
    host = f"{url.removeprefix('http://').removeprefix('https://')}:{port}"

    try:
        run_ollama_command("--version", host=host)
        models = running_model_names(host)
        if models and verbose:
            print(f"Stopping running models: {' '.join(models)}")
        for model in models:
            run_ollama_command("stop", model, host=host)
    except FileNotFoundError:
        if verbose:
            print("ollama CLI not found; skipping model stop.")

    pids = find_ollama_listener_pids(port)
    if not pids:
        if verbose:
            print(f"No process is listening on port {port} (already stopped?).")
        return 0

    killed = False
    for pid in pids:
        try:
            proc = psutil.Process(pid)
        except psutil.Error:
            continue
        name = proc.name().lower()
        if "ollama" not in name:
            continue
        if verbose:
            print(f"Stopping ollama serve PID {pid} (port {port})")
        proc.terminate()
        killed = True

    _gone, alive = psutil.wait_procs(
        [psutil.Process(pid) for pid in pids if psutil.pid_exists(pid)],
        timeout=3.0,
    )
    for proc in alive:
        try:
            proc.kill()
        except psutil.Error:
            continue

    if verbose:
        if killed:
            print(f"Ollama server on {host} stopped.")
        else:
            print(f"No ollama serve process found on {host}.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(description="Cross-platform Ollama helper for BatLLM")
    parser.add_argument("action", choices=("install", "start", "stop"))
    parser.add_argument(
        "-c",
        "--config",
        default=str(CONFIG_PATH),
        help="Path to the BatLLM YAML config file.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print verbose status when stopping the service.",
    )
    parser.add_argument(
        "--reinstall",
        action="store_true",
        help="Launch the official installer even if Ollama is already installed.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the Ollama helper CLI."""
    require_supported_python()
    parser = build_parser()
    args = parser.parse_args(argv)
    config_path = Path(args.config).resolve()

    if args.action == "install":
        code, message = install_service(reinstall=args.reinstall)
        if message:
            stream = sys.stderr if code else sys.stdout
            print(message, file=stream)
        return code
    if args.action == "start":
        return start_service(config_path)
    return stop_service(config_path, verbose=args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
