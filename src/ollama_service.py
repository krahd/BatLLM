"""Cross-platform Ollama lifecycle helper for BatLLM."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import psutil
import yaml


MIN_PYTHON = (3, 10)
ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "src" / "configs" / "config.yaml"


def require_supported_python() -> None:
    """Exit early with a clear message on unsupported Python versions."""
    if sys.version_info >= MIN_PYTHON:
        return
    version = ".".join(str(part) for part in sys.version_info[:3])
    raise SystemExit(f"BatLLM requires Python 3.10 or newer. Detected Python {version}.")


def load_llm_config(path: Path = CONFIG_PATH) -> dict[str, str | int]:
    """Load the LLM configuration required to manage the local Ollama service."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    llm = data.get("llm") or {}
    return {
        "model": str(llm.get("model") or "").strip(),
        "url": str(llm.get("url") or "http://localhost").strip().rstrip("/"),
        "port": int(llm.get("port") or 11434),
    }


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


def run_ollama_command(*args: str, host: str | None = None) -> subprocess.CompletedProcess:
    """Run an Ollama CLI command and capture the result."""
    env = os.environ.copy()
    if host:
        env["OLLAMA_HOST"] = host
    return subprocess.run(
        ["ollama", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def start_detached_ollama_serve(host: str) -> subprocess.Popen:
    """Start ``ollama serve`` in the background for the current platform."""
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

    return subprocess.Popen(["ollama", "serve"], **kwargs)


def wait_until_ready(url: str, port: int, timeout_seconds: float = 60.0) -> None:
    """Wait until the Ollama HTTP API becomes reachable."""
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if server_is_up(url, port):
            return
        time.sleep(1)
    raise RuntimeError(f"ollama serve did not become ready at {url}:{port}/api/version")


def preload_model(url: str, port: int, model: str) -> None:
    """Warm the selected model through the local Ollama API."""
    json_post(
        endpoint_url(url, port, "/api/generate"),
        {"model": model, "keep_alive": "30m"},
        timeout=60.0,
    )


def start_service(config_path: Path = CONFIG_PATH) -> int:
    """Start Ollama if needed, ensure the configured model is present, and warm it."""
    llm = load_llm_config(config_path)
    model = str(llm["model"])
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

    preload_model(url, port, model)

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


def find_ollama_listener_pids(port: int) -> list[int]:
    """Return process IDs listening on the configured TCP port."""
    pids: set[int] = set()
    for conn in psutil.net_connections(kind="inet"):
        if conn.status != psutil.CONN_LISTEN or not conn.laddr:
            continue
        if conn.laddr.port != port or conn.pid is None:
            continue
        pids.add(conn.pid)
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

    gone, alive = psutil.wait_procs(
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
    parser.add_argument("action", choices=("start", "stop"))
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
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the Ollama helper CLI."""
    require_supported_python()
    parser = build_parser()
    args = parser.parse_args(argv)
    config_path = Path(args.config).resolve()

    if args.action == "start":
        return start_service(config_path)
    return stop_service(config_path, verbose=args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
