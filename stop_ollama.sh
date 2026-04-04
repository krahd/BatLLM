#!/usr/bin/env bash
set -euo pipefail

exec python3 src/ollama_service.py stop "$@"
