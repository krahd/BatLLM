#!/usr/bin/env bash
set -euo pipefail

# BatLLM Ollama Runner
# This script starts an Ollama instance (if not already serving) and runs a specified model.
# It reads llm.model, llm.url, and llm.port from a YAML config.
#
# Defaults:
#   Config file: ./src/configs/config.yaml
#   Log file:    ./logs/b_ollama_<timestamp>.log
#
# Usage:
#   ./start_ollama.sh [-c <config.yaml>] [-l <logfile>] [-v] [-h]
#     -c  Path to YAML config (default: ./src/configs/config.yaml)
#     -l  Log file (append). If omitted and -v not set, default timestamped log is used.
#     -v  Verbose (no redirection; print to console)
#     -h  Help

CONFIG_FILE="./src/configs/config.yaml"
TIMESTAMP="$(date +'%Y%m%d_%H%M%S')"
LOG_FILE="./logs/b_ollama_${TIMESTAMP}.log"
VERBOSE=0

usage() {
  echo "BatLLM Ollama Runner"
  echo "This script starts an Ollama instance and runs a specified model."
  echo
  echo "Usage: $0 [-c <config.yaml>] [-l <logfile>] [-v]"
  echo "  -c  Path to YAML config (default: ${CONFIG_FILE})"
  echo "  -l  Log file (default: ${LOG_FILE})"
  echo "  -v  Verbose (no output redirection)"
  echo "  -h  Help"
  exit 1
}

while getopts ":c:l:vh" opt; do
  case "$opt" in
    c) CONFIG_FILE="$OPTARG" ;;
    l) LOG_FILE="$OPTARG" ;;
    v) VERBOSE=1 ;;
    h) usage ;;
    \?) echo "Unknown option: -$OPTARG" >&2; usage ;;
    :)  echo "Option -$OPTARG requires an argument." >&2; usage ;;
  esac
done

[ -f "$CONFIG_FILE" ] || { echo "Config not found: $CONFIG_FILE" >&2; exit 1; }

# --- Parse YAML (BSD awk safe). Expect:
# llm:
#   model: llama3:2latest
#   url:   http://localhost
#   port:  11434
parse_yaml_llm() {
  /usr/bin/awk '
    function trim(s) { gsub(/^[ \t"'\''"]+|[ \t"'\''"]+$/, "", s); return s }
    BEGIN { inside=0; base_indent=-1 }
    {
      match($0, /^[ \t]*/); lead = RLENGTH;

      if ($0 ~ /^[ \t]*llm:[ \t]*$/) { inside=1; base_indent=lead; next }
      if (inside && lead <= base_indent && $0 !~ /^[ \t]*$/) { inside=0 }

      if (inside) {
        line=$0
        if (line ~ /^[ \t]*model:[ \t]*/) { sub(/^[ \t]*model:[ \t]*/, "", line); print "MODEL=\"" trim(line) "\"" }
        else if (line ~ /^[ \t]*url:[ \t]*/) { sub(/^[ \t]*url:[ \t]*/, "", line); print "URL=\"" trim(line) "\"" }
        else if (line ~ /^[ \t]*port:[ \t]*/) { sub(/^[ \t]*port:[ \t]*/, "", line); print "PORT=\"" trim(line) "\"" }
      }
    }
  ' "$CONFIG_FILE"
}
eval "$(parse_yaml_llm)"

: "${MODEL:?Failed to read llm.model from $CONFIG_FILE}"
: "${URL:?Failed to read llm.url from $CONFIG_FILE}"
: "${PORT:?Failed to read llm.port from $CONFIG_FILE}"

HOST="${URL#http://}"; HOST="${HOST#https://}"; HOST="${HOST%%/}"

# logging helpers (no arrays / no eval)
init_logging() {
  if [[ "$VERBOSE" -eq 0 ]]; then
    mkdir -p "$(dirname "$LOG_FILE")"
  fi
}
say() {
  if [[ "$VERBOSE" -eq 1 ]]; then
    echo "$@"
  else
    printf '%s\n' "$@" >>"$LOG_FILE"
  fi
}
run_bg_logged() {
  if [[ "$VERBOSE" -eq 1 ]]; then
    nohup "$@" >/dev/stdout 2>/dev/stderr &
  else
    nohup "$@" >>"$LOG_FILE" 2>&1 &
  fi
}
run_logged() {
  if [[ "$VERBOSE" -eq 1 ]]; then
    "$@"
  else
    "$@" >>"$LOG_FILE" 2>&1
  fi
}

is_up() { curl -fsS "http://$HOST:$PORT/api/version" >/dev/null 2>&1; }
wait_ready() {
  local tries=60 ep="http://$HOST:$PORT/api/version"
  until curl -fsS "$ep" >/dev/null 2>&1; do
    tries=$((tries-1))
    if (( tries == 0 )); then
      echo "ollama serve did not become ready at $ep" >&2
      exit 1
    fi
    sleep 1
  done
}

init_logging
say "Config: model=$MODEL host=$HOST port=$PORT"

# Start server if needed
if is_up; then
  say "ollama already serving at $HOST:$PORT"
else
  say "Starting ollama serve at $HOST:$PORT ..."
  OLLAMA_HOST="$HOST:$PORT" run_bg_logged ollama serve
  wait_ready
  say "ollama is ready at $HOST:$PORT"
fi

# Load the model without starting a chat
say "Loading model into memory: $MODEL"
export OLLAMA_HOST="$HOST:$PORT"

# Pull the model (downloads and prepares if not present)
run_logged ollama pull "$MODEL"

# Optionally start it briefly to warm it up, then exit immediately
say "Warming up model: $MODEL"
run_logged ollama run "$MODEL" <<< ""