"""Ollama service operations using BatLLM configuration and process ownership.

Modelito supplies explicit-endpoint HTTP helpers and remote catalogue parsing.
Lifecycle policy and bounded local commands belong to BatLLM.
"""

from __future__ import annotations

from typing import Any, Mapping
import json
import math
import hashlib
import tempfile
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
import argparse

from util.paths import resolve_config_path, configured_batllm_home, default_batllm_home

_logger = logging.getLogger(__name__)

try:
    from modelito import ollama_service as _MODELITO  # type: ignore
    from modelito import Client, normalize_metadata  # type: ignore
except Exception as exc:  # pragma: no cover - environment misconfiguration
    raise RuntimeError("`modelito` is required for `llm.service`; install modelito") from exc


# Paths and defaults (shipped config + remote timeout catalog)
ROOT = Path(__file__).resolve().parents[2]
SHIPPED_CONFIG_PATH = ROOT / "src" / "configs" / "config.yaml"
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
DEFAULT_WARMUP_TIMEOUT = 30.0


# Compatibility names expected by tests and other modules
CONFIG_PATH = resolve_config_path(SHIPPED_CONFIG_PATH)

# Export a module-level `psutil` for tests that monkeypatch it. If unavailable,
# set to None — callers should handle the absence where appropriate.
try:
    import psutil  # type: ignore
except Exception:
    psutil = None  # type: ignore


def default_config_path() -> Path:
    """Return the active runtime config path for the current process."""
    return resolve_config_path(SHIPPED_CONFIG_PATH)


def load_config_data(path: Path | None = None) -> dict[str, Any]:
    """Load the shipped config plus any active user overlay config."""
    from configs.app_config import load_config_data as load_preferences
    return load_preferences(path, shipped_path=SHIPPED_CONFIG_PATH)


def load_llm_config(path: Path | None = None) -> dict[str, Any]:
    """Resolve service configuration exclusively from BatLLM preferences."""
    llm = load_config_data(path).get("llm", {})
    return {
        "timeout": llm.get("timeout"),
        "warmup_timeout": llm.get("warmup_timeout"),
        "last_served_model": str(llm.get("last_served_model") or "").strip(),
        "model": str(llm.get("model") or "").strip(),
        "model_timeouts": dict(llm.get("model_timeouts") or {}),
        "url": str(llm.get("url") or "http://localhost").rstrip("/"),
        "port": int(llm.get("port") or 11434),
    }


def _parse_positive_timeout(raw_timeout: Any) -> float | None:
    try:
        timeout = float(raw_timeout)
    except (TypeError, ValueError):
        return None
    return timeout if math.isfinite(timeout) and timeout > 0 else None


def common_model_timeout(model_name: str) -> float | None:
    normalized = str(model_name or "").strip()
    if not normalized:
        return None
    if normalized in COMMON_MODEL_TIMEOUTS:
        return COMMON_MODEL_TIMEOUTS[normalized]
    family = normalized.split(":", 1)[0]
    return COMMON_MODEL_TIMEOUTS.get(family)


def resolve_warmup_timeout(llm: Mapping[str, Any], default: float = DEFAULT_WARMUP_TIMEOUT) -> float:
    timeout = _parse_positive_timeout(llm.get("warmup_timeout"))
    if timeout is not None:
        return timeout
    return float(default)


def lookup_model_metadata(
    model: str | None = None,
    *,
    host: str | None = None,
    port: int | None = None,
) -> dict[str, Any]:
    llm = load_llm_config()
    selected_model = str(model or llm.get("model") or "").strip()
    if not selected_model:
        return {}
    base_url = str(host or llm.get("url") or "http://localhost").rstrip("/")
    resolved_port = int(port or llm.get("port") or 11434)
    try:
        client = Client(provider="ollama", model=selected_model, host=base_url, port=resolved_port)
        raw = client.model_metadata(model=selected_model)
        return normalize_metadata(raw)
    except Exception:
        return {}


def build_saved_llm_metadata_snapshot(path: Path | None = None) -> dict[str, Any]:
    data = load_config_data(path)
    llm = data.get("llm") or {}
    config_llm = llm
    selected_model = str(config_llm.get("model") or "").strip()
    last_served_model = str(config_llm.get("last_served_model") or "").strip()
    snapshot = {
        "configured_model": selected_model,
        "last_served_model": last_served_model,
        "request_timeout": resolve_request_timeout(config_llm, model=selected_model) if selected_model else None,
        "warmup_timeout": resolve_warmup_timeout(config_llm),
        "url": str(config_llm.get("url") or "http://localhost"),
        "port": int(config_llm.get("port") or 11434),
        "config_snapshot": {
            "num_ctx": llm.get("num_ctx"),
            "num_predict": llm.get("num_predict"),
            "num_thread": llm.get("num_thread"),
            "max_tokens": llm.get("max_tokens"),
            "temperature": llm.get("temperature"),
            "top_k": llm.get("top_k"),
            "top_p": llm.get("top_p"),
            "path": llm.get("path"),
        },
        "provider_metadata": {},
    }
    snapshot["config_snapshot"] = {
        key: value for key, value in snapshot["config_snapshot"].items() if value is not None
    }
    return snapshot


def load_remote_timeout_catalog(path: Path = REMOTE_TIMEOUT_CATALOG_PATH) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _parse_model_scale_billions(size_label: str) -> float | None:
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
                source = str(band.get("source") or f"the {band_limit:g}B remote size band")
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
    timeout, _source = resolve_request_timeout_details(llm, default=default, model=model)
    return timeout


def preferred_start_model(llm: Mapping[str, Any]) -> str:
    last_served_model = str(llm.get("last_served_model") or "").strip()
    model = str(llm.get("model") or "").strip()
    return last_served_model or model


def save_last_served_model(model: str, path: Path | None = None) -> None:
    """Persist service preferences through the guarded atomic config writer."""
    from configs.app_config import AppConfig  # pylint: disable=import-outside-toplevel

    resolved_path = default_config_path() if path is None else path
    preferences = AppConfig(path=resolved_path, default_path=SHIPPED_CONFIG_PATH)
    preferences.set("llm", "last_served_model", model.strip())
    preferences.save()


def ollama_binary_candidates() -> list[Path]:
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
        candidates.extend([
            Path("/Applications/Ollama.app/Contents/Resources/ollama"),
            Path("/Applications/Ollama.app/Contents/MacOS/Ollama"),
            Path("/usr/local/bin/ollama"),
            Path("/opt/homebrew/bin/ollama"),
        ])
    else:
        candidates.extend([Path("/usr/local/bin/ollama"),
                          Path("/usr/bin/ollama"), Path("/bin/ollama")])
    unique: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        unique.append(candidate)
    return unique


def resolve_ollama_command() -> str:
    try:
        resolver = getattr(_MODELITO, "resolve_ollama_command", None)
        if callable(resolver):
            return resolver()
    except Exception:
        pass
    for candidate in ollama_binary_candidates():
        if candidate.exists():
            return str(candidate)
    raise FileNotFoundError("ollama")


def ollama_installed() -> bool:
    try:
        resolve_ollama_command()
        return True
    except FileNotFoundError:
        return False


def install_command_for_current_platform(platform_name: str | None = None) -> tuple[list[str], str]:
    selected_platform = platform_name or sys.platform
    if platform_name is None:
        try:
            helper = getattr(_MODELITO, "install_command_for_current_platform", None)
            if callable(helper):
                return helper(None)
        except Exception:
            pass

    if selected_platform.startswith("win"):
        command = [
            "powershell.exe",
            "-NoExit",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            f"irm {WINDOWS_INSTALL_URL} | iex",
        ]
        return command, f"irm {WINDOWS_INSTALL_URL} | iex"
    if selected_platform == "darwin":
        return ["brew", "install", "ollama"], "brew install ollama"
    install_command = f"export OLLAMA_NO_START=1; curl -fsSL {shlex.quote(UNIX_INSTALL_URL)} | sh"
    return ["/bin/sh", "-lc", install_command], install_command


def ollama_version_text(host: str | None = None) -> str:
    try:
        proc = run_ollama_command("--version", host=host)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
    return ((proc.stdout or "") + (proc.stderr or "")).strip()


def install_service(reinstall: bool = False) -> tuple[int, str]:
    import webbrowser
    del reinstall
    url = "https://ollama.com/download"
    if not webbrowser.open(url):
        return 1, f"Open {url} to install Ollama."
    return 0, "Opened the official Ollama download page. Complete installation, then refresh BatLLM."


def endpoint_url(url: str, port: int, path: str) -> str:
    fn = getattr(_MODELITO, "endpoint_url", None)
    if callable(fn):
        return fn(url, port, path)
    return f"{url}:{port}{path}"


def json_get(url: str, timeout: float = 5.0) -> dict:
    fn = getattr(_MODELITO, "json_get", None)
    if callable(fn):
        return fn(url, timeout=timeout)
    raise RuntimeError("modelito.json_get is unavailable")


def json_post(url: str, payload: dict, timeout: float = 60.0) -> dict:
    fn = getattr(_MODELITO, "json_post", None)
    if callable(fn):
        return fn(url, payload, timeout=timeout)
    raise RuntimeError("modelito.json_post is unavailable")


def server_is_up(url: str, port: int) -> bool:
    fn = getattr(_MODELITO, "server_is_up", None)
    if callable(fn):
        return bool(fn(url, port))
    return False


def inspect_service_state(config_path: Path | None = None) -> dict[str, object]:
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
    env = os.environ.copy()
    if host:
        env["OLLAMA_HOST"] = host
    command = resolve_ollama_command()
    return subprocess.run([command, *args], cwd=ROOT, text=True, capture_output=True, check=False, env=env, timeout=600.0 if args and args[0] == "pull" else 30.0, encoding="utf-8")


def start_detached_ollama_serve(host: str) -> subprocess.Popen:
    command = resolve_ollama_command()
    kwargs: dict[str, object] = {"cwd": ROOT, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL,
                                 "stdin": subprocess.DEVNULL, "env": {**os.environ, "OLLAMA_HOST": host}, "text": True}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
    else:
        kwargs["start_new_session"] = True
    process = subprocess.Popen([command, "serve"], **kwargs)
    try:
        _record_owned_server(host, process.pid)
    except Exception:
        process.terminate()
        process.wait(timeout=3.0)
        raise
    return process


def wait_until_ready(url: str, port: int, timeout_seconds: float = 60.0) -> None:
    fn = getattr(_MODELITO, "wait_until_ready", None)
    if callable(fn):
        fn(url, port, timeout_seconds=timeout_seconds)
        return
    raise RuntimeError("modelito.wait_until_ready is unavailable")


def preload_model(url: str, port: int, model: str, timeout: float = 120.0) -> None:
    fn = getattr(_MODELITO, "preload_model", None)
    if callable(fn):
        fn(url, port, model, timeout=timeout)
        return
    raise RuntimeError("modelito.preload_model is unavailable")


def start_service(config_path: Path | None = None, warmup_timeout: float | None = None) -> int:
    # Lifecycle decisions use only the resolved BatLLM configuration.
    llm = load_llm_config(config_path)
    resolved_warmup_timeout = resolve_warmup_timeout(
        llm, default=DEFAULT_WARMUP_TIMEOUT) if warmup_timeout is None else float(warmup_timeout)
    if _parse_positive_timeout(resolved_warmup_timeout) is None:
        raise ValueError("Warmup timeout must be finite and positive")
    model = preferred_start_model(llm)
    timeout = resolve_request_timeout(llm, model=model)

    url = str(llm["url"])
    port = int(llm["port"])
    host = f"{url.removeprefix('http://').removeprefix('https://')}:{port}"
    model_provided = bool(model)
    if not model_provided:
        print(
            f"No model configured in {config_path}; starting Ollama without preloading a model.",
            file=sys.stderr,
        )
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
        wait_until_ready(url, port, timeout_seconds=resolved_warmup_timeout)
        started = True
        print(f"Ollama is ready at {host}")
    if model_provided:
        pull_proc = run_ollama_command("pull", model, host=host)
        if pull_proc.returncode != 0:
            sys.stderr.write((pull_proc.stdout or "") + (pull_proc.stderr or ""))
            return pull_proc.returncode
        preload_model(url, port, model, timeout=timeout)
        save_last_served_model(model, config_path)
        if started:
            print(f"Completed: started ollama at {host}, pulled and warmed model '{model}'.")
        else:
            print(
                f"Completed: ollama already running at {host}; pulled and warmed model '{model}'.")
        return 0
    # No model configured: server started (or already running), nothing more to do.
    if started:
        print(f"Completed: started ollama at {host} (no model configured).")
    else:
        print(f"Ollama already running at {host} (no model configured).")
    return 0


def running_model_names(host: str) -> list[str]:
    url = host if "://" in host else f"http://{host}"
    return [entry["name"] for entry in json_get(f"{url}/api/ps").get("models", [])]


def _management_client(timeout=30.0):
    from ollama import Client as OllamaClient
    llm = load_llm_config()
    return OllamaClient(host=endpoint_url(llm["url"], llm["port"], ""), timeout=timeout)


def list_local_models():
    """List only the explicitly configured endpoint's local inventory."""
    llm = load_llm_config()
    payload = json_get(endpoint_url(llm["url"], llm["port"], "/api/tags"))
    return [name for entry in payload.get("models", [])
            if isinstance(entry, dict)
            and isinstance(name := entry.get("name") or entry.get("model"), str) and name]


def list_remote_model_catalog():
    """Bound Modelito's remote catalogue lookup in a separate process."""
    from types import SimpleNamespace
    code = (
        "import json; from dataclasses import asdict; "
        "from modelito import ollama_service as m; "
        "m.list_local_models = lambda: []; "
        "print(json.dumps([asdict(e) for e in m.list_remote_model_catalog()]))"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True,
                            text=True, encoding="utf-8", check=True, timeout=30.0)
    installed = set(list_local_models())
    entries = json.loads(result.stdout)
    return [SimpleNamespace(**{**entry, "installed": entry["name"] in installed})
            for entry in entries]


def download_model_progress(model_name: str, timeout: float = 600.0):
    """Pull through the configured endpoint, with an overall deadline."""
    from types import SimpleNamespace
    started = time.monotonic()
    for event in _management_client(timeout=timeout).pull(model_name, stream=True):
        if time.monotonic() - started > timeout:
            raise TimeoutError(f"Model download exceeded {timeout:g}s")
        total = event.total or 0
        yield SimpleNamespace(model=model_name, phase=event.status, message=event.status,
                              progress=(event.completed or 0) / total if total else 0,
                              error=None)


def delete_model(model_name: str) -> bool:
    _management_client().delete(model_name)
    return True


def find_ollama_listener_pids(port: int) -> list[int]:
    # Prefer to use the module-level psutil (so tests can monkeypatch it).
    psmod = psutil
    if psmod is None:
        try:
            import psutil as _pslocal  # type: ignore

            psmod = _pslocal
        except Exception:
            psmod = None

    def _listener_pids_from_connections(connections, port: int) -> list[int]:
        pids: set[int] = set()
        for conn in connections:
            if conn.status != psmod.CONN_LISTEN or not conn.laddr:
                continue
            if conn.laddr.port != port or conn.pid is None:
                continue
            pids.add(conn.pid)
        return sorted(pids)

    if psmod is not None:
        try:
            return _listener_pids_from_connections(psmod.net_connections(kind="inet"), port)
        except Exception:
            # fall back to scanning processes
            pass

    # If psutil is entirely unavailable, prefer modelito's helper (it uses system
    # psutil) as a last resort. Otherwise, do a process-scan fallback.
    try:
        finder = getattr(_MODELITO, "find_ollama_listener_pids", None)
        if callable(finder) and psmod is None:
            return finder(port)
    except Exception:
        pass

    if psmod is None:
        return []

    pids: set[int] = set()
    for proc in psmod.process_iter(["pid", "name"]):
        try:
            name = str((proc.info or {}).get("name") or proc.name()).lower()
        except Exception:
            continue
        if "ollama" not in name:
            continue
        try:
            connections = proc.net_connections(kind="inet")
        except Exception:
            continue
        for conn in connections:
            if conn.status != psmod.CONN_LISTEN or not conn.laddr:
                continue
            if conn.laddr.port != port:
                continue
            pids.add(getattr(conn, "pid", None) or proc.pid)
    return sorted(pids)


def _ownership_path(host: str) -> Path:
    home = configured_batllm_home() or default_batllm_home()
    key = hashlib.sha256(host.encode("utf-8")).hexdigest()[:24]
    return home / f"ollama-owned-{key}.json"


def _record_owned_server(host: str, pid: int) -> None:
    """Record PID and birth time; PID reuse must never authorise termination."""
    if psutil is None:
        raise RuntimeError("psutil is required to track service ownership")
    process = psutil.Process(pid)
    path = _ownership_path(host)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".ollama-owned-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump({"host": host, "pid": pid, "created": process.create_time()}, handle)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def stop_service(config_path: Path | None = None, verbose: bool = False) -> int:
    """Stop only a server launched by BatLLM, verified against its birth time."""
    llm = load_llm_config(config_path)
    host = f"{str(llm['url']).removeprefix('http://').removeprefix('https://')}:{llm['port']}"
    path = _ownership_path(host)
    if not path.exists():
        if verbose:
            print(f"No BatLLM-owned server at {host}; external service left running.")
        return 0
    if psutil is None:
        return 1
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
        process = psutil.Process(record["pid"])
        if (record["host"] != host or process.create_time() != record["created"]
                or "ollama" not in process.name().lower()
                or "serve" not in process.cmdline()):
            return 1
        process.terminate()
        try:
            process.wait(timeout=3.0)
        except psutil.TimeoutExpired:
            process.kill()
            process.wait(timeout=3.0)
    except psutil.NoSuchProcess:
        pass
    except (OSError, ValueError, KeyError, psutil.Error):
        return 1
    path.unlink(missing_ok=True)
    return 0


def build_parser() -> 'argparse.ArgumentParser':
    import argparse
    parser = argparse.ArgumentParser(description="Centralized Ollama/modelito helper")
    parser.add_argument("action", choices=("install", "start", "stop"))
    parser.add_argument(
        "-c",
        "--config",
        default=None,
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
    parser.add_argument(
        "--warmup-timeout",
        type=float,
        default=None,
        help="Override the Ollama service warmup timeout in seconds for this start operation.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config_path = Path(args.config).resolve() if args.config else None
    if args.action == "install":
        code, message = install_service(reinstall=args.reinstall)
        if message:
            stream = sys.stderr if code else sys.stdout
            print(message, file=stream)
        return code
    if args.action == "start":
        return start_service(config_path, warmup_timeout=args.warmup_timeout)
    return stop_service(config_path, verbose=args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
