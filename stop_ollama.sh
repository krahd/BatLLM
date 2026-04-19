#!/usr/bin/env bash
set -euo pipefail

# Stop Ollama via the centralized llm.service module
exec python3 -m llm.service stop "$@"
