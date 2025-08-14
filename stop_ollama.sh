#!/bin/bash

# This script stops the Ollama instance running
# Set port

PORT=$(cat src/configs/config.yaml | grep 'port' | awk '{print $2}')

pkill -f "OLLAMA_HOST=localhost:$PORT"
echo "Ollama on port $PORT has been stopped."
