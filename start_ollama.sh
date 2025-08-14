#!/bin/bash
# Starts an instance of Ollama
# Normally BatLLM itself runs this if it does not find Ollama running on the port specified in configs/config.yaml.

PORT=$(cat src/configs/config.yaml | grep 'port' | awk '{print $2}')
if [ -z "$PORT" ]; then
  echo "Error: Could not extract port from ./src/configs/config.yaml"
  exit 1
fi

echo "Starting Ollama on port $PORT..."

if [ "$1" == "-l" ]; then    
    TS=$(date +"%Y%m%d_%H%M%S")
    LOG=$(echo "b_"$TS".log")    
    OLLAMA_HOST=localhost:$PORT ollama serve > "$LOG" & # 2>&1)
    echo "($LOG)"
else
    OLLAMA_HOST=localhost:$PORT ollama serve & # 2>&1)
fi
