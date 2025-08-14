#!/usr/bin/env bash
set -euo pipefail

# BatLLM Ollama Stopper
# This script attempts to stop running models and the Ollama server
# bound to the host:port defined in the YAML config.
#
# Defaults:
#   Config file: ./src/configs/config.yaml
#
# Usage:
#   ./stop_ollama.sh [-c <config.yaml>] [-v] [-h]
#     -c  Path to YAML config (default: ./src/configs/config.yaml)
#     -v  Verbose (print actions)
#     -h  Help

CONFIG_FILE="./src/configs/config.yaml"
VERBOSE=0

usage() {
  echo "BatLLM Ollama Stopper"
  echo "This script stops running Ollama models and the server from the configured port."
  echo
  echo "Usage: $0 [-c <config.yaml>] [-v]"
  echo "  -c  Path to YAML config (default: ${CONFIG_FILE})"
  echo "  -v  Verbose output"
  echo "  -h  Help"
  exit 1
}

while getopts ":c:vh" opt; do
  case "$opt" in
    c) CONFIG_FILE="$OPTARG" ;;
    v) VERBOSE=1 ;;
    h) usage ;;
    \?) echo "Unknown option: -$OPTARG" >&2; usage ;;
    :)  echo "Option -$OPTARG requires an argument." >&2; usage ;;
  esac
done

[ -f "$CONFIG_FILE" ] || { echo "Config not found: $CONFIG_FILE" >&2; exit 1; }

parse_yaml_llm() {
  /usr/bin/awk '
    function trim(s) { gsub(/^[ \t"'\''"]+|[ \t"'\''"]+$/, "", s); return s }
    BEGIN { inside=0; llm_indent=-1 }
    {
      match($0, /^[ \t]*/); lead = RLENGTH;
      if ($0 ~ /^[ \t]*llm:[ \t]*$/) { inside=1; llm_indent=lead; next }
      if (inside && lead <= llm_indent && $0 !~ /^[ \t]*$/) { inside=0 }
      if (inside) {
        line=$0
        if (line ~ /^[ \t]*url:[ \t]*/)  { sub(/^[ \t]*url:[ \t]*/, "", line);  line=trim(line); print "URL=\"" line "\"" }
        if (line ~ /^[ \t]*port:[ \t]*/) { sub(/^[ \t]*port:[ \t]*/, "", line); line=trim(line); print "PORT=\"" line "\"" }
      }
    }
  ' "$CONFIG_FILE"
}
eval "$(parse_yaml_llm)"

: "${URL:?Failed to read llm.url from $CONFIG_FILE}"
: "${PORT:?Failed to read llm.port from $CONFIG_FILE}"

HOST="${URL#http://}"; HOST="${HOST#https://}"; HOST="${HOST%%/}"

say() { if [[ "$VERBOSE" -eq 1 ]]; then echo "$@"; fi }

# Try to stop running models gracefully (via CLI)
if command -v ollama >/dev/null 2>&1; then
  export OLLAMA_HOST="$HOST:$PORT"
  if ollama ps >/dev/null 2>&1; then
    # shellcheck disable=SC2207
    MODELS=( $(ollama ps | awk 'NR>1 {print $1}') )
    if [[ ${#MODELS[@]} -gt 0 ]]; then
      say "Stopping running models: ${MODELS[*]}"
      for m in "${MODELS[@]}"; do
        ollama stop "$m" >/dev/null 2>&1 || true
      done
    else
      say "No running models reported by ollama ps."
    fi
  fi
else
  say "ollama CLI not found; skipping model stop."
fi

# Kill the server listening on the configured port
PIDS="$(lsof -nP -iTCP:"$PORT" -sTCP:LISTEN -t 2>/dev/null || true)"
if [[ -z "$PIDS" ]]; then
  say "No process is listening on port $PORT (already stopped?)."
  exit 0
fi

KILLED=0
for pid in $PIDS; do
  if ps -p "$pid" -o comm= | grep -qi "ollama"; then
    say "Killing ollama serve PID $pid (port $PORT)"
    kill "$pid" || true
    KILLED=1
  fi
done

sleep 1
for pid in $PIDS; do
  if ps -p "$pid" >/dev/null 2>&1; then
    say "Force killing PID $pid"
    kill -9 "$pid" || true
  fi
done

if [[ "$KILLED" -eq 1 ]]; then
  say "Ollama server on $HOST:$PORT stopped."
else
  say "No ollama serve process found on $HOST:$PORT."
fi