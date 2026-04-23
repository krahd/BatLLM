"""Centralized Modelito-based Ollama lifecycle helpers and BatLLM LLM helpers.

This module delegates lifecycle operations to `modelito.ollama_service` and
exposes the small set of BatLLM-specific helper utilities (timeouts, config
loading, and a few CLI helpers) that the UI and tests expect.

Modelito is required; this module re-exports commonly-used helpers and
implements BatLLM-specific behaviour where appropriate.
"""

from __future__ import annotations

from typing import Any, Mapping
import json
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml
import argparse

from util.paths import resolve_config_path

_logger = logging.getLogger(__name__)

try:
    from modelito import ollama_service as _MODELITO  # type: ignore
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
    resolved_path = default_config_path() if path is None else path
    data = yaml.safe_load(SHIPPED_CONFIG_PATH.read_text(encoding="utf-8")) or {}
    if resolved_path.exists() and resolved_path != SHIPPED_CONFIG_PATH:
        overlay = yaml.safe_load(resolved_path.read_text(encoding="utf-8")) or {}
        if isinstance(overlay, dict):
            for section, values in overlay.items():
                if section not in data:
                    data[section] = {}
                if isinstance(values, dict):
                    data[section].update(values)
                else:
                    data[section] = values
    return data if isinstance(data, dict) else {}


def load_llm_config(path: Path | None = None) -> dict[str, Any]:
    """Load the LLM configuration required to manage the local Ollama service.

    Behavior:
    - If `path` is None, prefer `modelito.load_llm_config()` to preserve modelito's
      default behaviour.
    - If `path` is provided, use the local shipped config (`SHIPPED_CONFIG_PATH`)
      plus any overlay at `path`. This ensures callers (and tests) that monkeypatch
      `SHIPPED_CONFIG_PATH` get the patched file.
    """
    if path is None:
        try:
            loader = getattr(_MODELITO, "load_llm_config", None)
            if callable(loader):
                return loader(None)
        except Exception:
            pass

    data = load_config_data(path)
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
    try:
        timeout = float(raw_timeout)
    except (TypeError, ValueError):
        return None
    return timeout if timeout > 0 else None


def common_model_timeout(model_name: str) -> float | None:
    normalized = str(model_name or "").strip()
    if not normalized:
        return None
    if normalized in COMMON_MODEL_TIMEOUTS:
        return COMMON_MODEL_TIMEOUTS[normalized]
    family = normalized.split(":", 1)[0]
    return COMMON_MODEL_TIMEOUTS.get(family)


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
    resolved_path = default_config_path() if path is None else path
    data = load_config_data(resolved_path)
    llm = data.setdefault("llm", {})
    llm["last_served_model"] = model.strip()
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


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
    try:
        helper = getattr(_MODELITO, "install_command_for_current_platform", None)
        if callable(helper):
            return helper(platform_name)
    except Exception:
        pass
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


def ollama_version_text(host: str | None = None) -> str:
    try:
        proc = run_ollama_command("--version", host=host)
    except FileNotFoundError:
        return ""
    return ((proc.stdout or "") + (proc.stderr or "")).strip()


def install_service(reinstall: bool = False) -> tuple[int, str]:
    try:
        installer = getattr(_MODELITO, "install_service", None)
        if callable(installer):
            return installer(reinstall=reinstall)
    except Exception:
        pass
    try:
        _cmd, display = install_command_for_current_platform()
        # Do not execute the installer automatically; return a launch message
        return 0, display
    except Exception as exc:
        return 1, str(exc)


def endpoint_url(url: str, port: int, path: str) -> str:
    try:
        fn = getattr(_MODELITO, "endpoint_url", None)
        if callable(fn):
            return fn(url, port, path)
    except Exception:
        pass
    return f"{url}:{port}{path}"


def json_get(url: str, timeout: float = 5.0) -> dict:
    with urlopen(url, timeout=timeout) as response:
        body = response.read().decode("utf-8")
    return json.loads(body) if body else {}


def json_post(url: str, payload: dict, timeout: float = 60.0) -> dict:
    request = Request(url, data=json.dumps(payload).encode("utf-8"),
                      headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8")
    return json.loads(body) if body else {}


def server_is_up(url: str, port: int) -> bool:
    try:
        json_get(endpoint_url(url, port, "/api/version"), timeout=2.0)
        return True
    except (URLError, HTTPError, ValueError):
        return False


def inspect_service_state(config_path: Path | None = None) -> dict[str, object]:
    try:
        inspector = getattr(_MODELITO, "inspect_service_state", None)
        if callable(inspector):
            return inspector(str(config_path) if config_path is not None else None)
    except Exception:
        pass
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
    try:
        runner = getattr(_MODELITO, "run_ollama_command", None)
        if callable(runner):
            return runner(*args, host=host)
    except Exception:
        pass
    env = os.environ.copy()
    if host:
        env["OLLAMA_HOST"] = host
    command = resolve_ollama_command()
    return subprocess.run([command, *args], cwd=ROOT, text=True, capture_output=True, check=False, env=env)


def start_detached_ollama_serve(host: str) -> subprocess.Popen:
    command = resolve_ollama_command()
    kwargs: dict[str, object] = {"cwd": ROOT, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL,
                                 "stdin": subprocess.DEVNULL, "env": {**os.environ, "OLLAMA_HOST": host}, "text": True}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
    else:
        kwargs["start_new_session"] = True
    return subprocess.Popen([command, "serve"], **kwargs)


def wait_until_ready(url: str, port: int, timeout_seconds: float = 60.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if server_is_up(url, port):
            return
        time.sleep(1)
    raise RuntimeError(f"ollama serve did not become ready at {url}:{port}/api/version")


def preload_model(url: str, port: int, model: str, timeout: float = 120.0) -> None:
    json_post(endpoint_url(url, port, "/api/generate"),
              {"model": model, "keep_alive": "30m"}, timeout=timeout)


def start_service(config_path: Path | None = None) -> int:
    # Prefer delegating to modelito when no explicit config path is provided; when
    # a `config_path` is given, run the local implementation so callers and tests
    # that monkeypatch module-level helpers are respected.
    if config_path is None:
        try:
            starter = getattr(_MODELITO, "start_service", None)
            if callable(starter):
                # Prefer delegating to modelito, but if it fails (non-zero),
                # fall back to the local implementation so BatLLM can still
                # attempt to start the Ollama server.
                try:
                    rc = starter(None)
                except Exception:
                    rc = 1
                if rc == 0:
                    return 0
                # fall through to local start implementation on non-zero rc
        except Exception:
            pass
    llm = load_llm_config(config_path)
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
        wait_until_ready(url, port)
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


def stop_service(config_path: Path | None = None, verbose: bool = False) -> int:
    # Prefer delegating to modelito when no explicit config path is provided.
    if config_path is None:
        try:
            stopper = getattr(_MODELITO, "stop_service", None)
            if callable(stopper):
                return stopper(None, verbose=verbose)
        except Exception:
            pass
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
    try:
        import psutil as _ps
    except Exception:
        _ps = None
    if _ps is None:
        return 0
    for pid in pids:
        try:
            proc = _ps.Process(pid)
        except _ps.Error:
            continue
        name = proc.name().lower()
        if "ollama" not in name:
            continue
        if verbose:
            print(f"Stopping ollama serve PID {pid} (port {port})")
        proc.terminate()
        killed = True
    _gone, alive = _ps.wait_procs([_ps.Process(pid)
                                  for pid in pids if _ps.pid_exists(pid)], timeout=3.0)
    for proc in alive:
        try:
            proc.kill()
        except _ps.Error:
            continue
    if verbose:
        if killed:
            print(f"Ollama server on {host} stopped.")
        else:
            print(f"No ollama serve process found on {host}.")
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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config_path = Path(args.config).resolve() if args.config else None
    if args.action == "install":
        try:
            installer = getattr(_MODELITO, "install_service", None)
            if callable(installer):
                code, message = installer(reinstall=args.reinstall)
            else:
                code, message = install_command_for_current_platform()
        except Exception:
            code, message = install_command_for_current_platform()
        if message:
            stream = sys.stderr if code else sys.stdout
            print(message, file=stream)
        return code
    if args.action == "start":
        return start_service(config_path)
    return stop_service(config_path, verbose=args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
