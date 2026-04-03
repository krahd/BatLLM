#!/usr/bin/env bash
set -euo pipefail

# BatLLM test runner
# Modes:
#   core - non-interactive core smoke tests only
#   full - core + live Ollama smoke tests (starts/stops Ollama)

MODE="${1:-core}"
VENV_PYTHON="./.venv_BatLLM/bin/python"

usage() {
  echo "Usage: $0 [core|full]"
  echo "  core: run non-interactive smoke checks only"
  echo "  full: run all smoke checks including live Ollama integration tests"
}

if [[ "${MODE}" != "core" && "${MODE}" != "full" ]]; then
  usage
  exit 1
fi

if [[ ! -x "${VENV_PYTHON}" ]]; then
  echo "Error: ${VENV_PYTHON} not found or not executable." >&2
  echo "Create the venv first: python -m venv .venv_BatLLM" >&2
  exit 1
fi

run_pytest() {
  PYTHONPATH=src "${VENV_PYTHON}" -m pytest -q "$@"
}

if [[ "${MODE}" == "core" ]]; then
  run_pytest src/tests/test_history_compact.py
  exit 0
fi

cleanup() {
  ./stop_ollama.sh -v >/dev/null 2>&1 || true
}
trap cleanup EXIT

./start_ollama.sh
BATLLM_RUN_OLLAMA_SMOKE=1 run_pytest src/tests
