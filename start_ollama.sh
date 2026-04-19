#!/usr/bin/env bash
set -euo pipefail

# Start Ollama via the centralized llm.service module
exec python3 -m llm.service start "$@"
