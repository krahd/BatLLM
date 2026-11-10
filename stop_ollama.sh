#!/usr/bin/env bash
set -euo pipefail

# Stop Ollama via the centralized llm.service module.
# Works from any directory: the module lives in this checkout's src/ tree.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Prefer an explicit override, then the project environments, then a
# supported interpreter (BatLLM supports Python 3.10-3.12).
find_python() {
  if [ -n "${BATLLM_PYTHON:-}" ]; then
    printf '%s\n' "$BATLLM_PYTHON"
    return 0
  fi
  local candidate
  for candidate in \
    "$SCRIPT_DIR/.venv_BatLLM/bin/python" \
    "$SCRIPT_DIR/.venv/bin/python"; do
    if [ -x "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  for candidate in python3.12 python3.11 python3.10 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  echo "No Python interpreter found. Install Python 3.10-3.12 or set BATLLM_PYTHON." >&2
  return 1
}

PYTHON="$(find_python)"
export PYTHONPATH="$SCRIPT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$PYTHON" -m llm.service stop "$@"
