"""Compatibility wrapper that re-exports the canonical `llm.service` API.

Historically BatLLM provided a standalone `ollama_service` module. As part of
the modelito migration the authoritative implementation lives in
`llm.service`. This file keeps the legacy import surface by delegating all
symbols to `llm.service` so callers and tests continue to work unchanged.
"""

from __future__ import annotations

from typing import Any, Mapping
from pathlib import Path

from llm import service as _service

# Re-export constants
SHIPPED_CONFIG_PATH = _service.SHIPPED_CONFIG_PATH
REMOTE_TIMEOUT_CATALOG_PATH = getattr(_service, "REMOTE_TIMEOUT_CATALOG_PATH", None)
UNIX_INSTALL_URL = getattr(_service, "UNIX_INSTALL_URL", "https://ollama.com/install.sh")
WINDOWS_INSTALL_URL = getattr(_service, "WINDOWS_INSTALL_URL", "https://ollama.com/install.ps1")
COMMON_MODEL_TIMEOUTS = getattr(_service, "COMMON_MODEL_TIMEOUTS", {})
CONFIG_PATH = getattr(_service, "CONFIG_PATH", None)

# Core helpers
default_config_path = _service.default_config_path
load_config_data = _service.load_config_data
load_llm_config = _service.load_llm_config
common_model_timeout = _service.common_model_timeout
load_remote_timeout_catalog = _service.load_remote_timeout_catalog
estimate_remote_model_timeout_details = _service.estimate_remote_model_timeout_details
resolve_request_timeout_details = _service.resolve_request_timeout_details
resolve_request_timeout = _service.resolve_request_timeout
preferred_start_model = _service.preferred_start_model
save_last_served_model = _service.save_last_served_model

# CLI / lifecycle helpers
ollama_binary_candidates = _service.ollama_binary_candidates
resolve_ollama_command = _service.resolve_ollama_command
ollama_installed = _service.ollama_installed
install_command_for_current_platform = _service.install_command_for_current_platform
install_service = _service.install_service
endpoint_url = _service.endpoint_url
json_get = _service.json_get
json_post = _service.json_post
server_is_up = _service.server_is_up
inspect_service_state = _service.inspect_service_state
run_ollama_command = _service.run_ollama_command
start_detached_ollama_serve = _service.start_detached_ollama_serve
wait_until_ready = _service.wait_until_ready
preload_model = _service.preload_model
start_service = _service.start_service
running_model_names = _service.running_model_names
find_ollama_listener_pids = _service.find_ollama_listener_pids
stop_service = _service.stop_service

# CLI entrypoint
build_parser = _service.build_parser
main = _service.main

# Expose psutil (if present in llm.service) for tests that monkeypatch it.
psutil = getattr(_service, "psutil", None)

__all__ = [
    "SHIPPED_CONFIG_PATH",
    "REMOTE_TIMEOUT_CATALOG_PATH",
    "UNIX_INSTALL_URL",
    "WINDOWS_INSTALL_URL",
    "COMMON_MODEL_TIMEOUTS",
    "CONFIG_PATH",
    "default_config_path",
    "load_config_data",
    "load_llm_config",
    "common_model_timeout",
    "load_remote_timeout_catalog",
    "estimate_remote_model_timeout_details",
    "resolve_request_timeout_details",
    "resolve_request_timeout",
    "preferred_start_model",
    "save_last_served_model",
    "ollama_binary_candidates",
    "resolve_ollama_command",
    "ollama_installed",
    "install_command_for_current_platform",
    "install_service",
    "endpoint_url",
    "json_get",
    "json_post",
    "server_is_up",
    "inspect_service_state",
    "run_ollama_command",
    "start_detached_ollama_serve",
    "wait_until_ready",
    "preload_model",
    "start_service",
    "running_model_names",
    "find_ollama_listener_pids",
    "stop_service",
    "build_parser",
    "main",
    "psutil",
]
