#!/bin/bash

# This script stops the Ollama instance running
# Set port
PORT=$(grep '^port:' configs/config.yaml | awk '{print $2}')

pkill -f "OLLAMA_HOST=localhost:$PORT"
echo "Ollama on port $PORT has been stopped."
