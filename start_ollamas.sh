#!/bin/bash

# Set ports
PORT1=5001
PORT2=5002

# Function to start Ollama on a given port
start_ollama_instance() {
  local PORT=$1
  echo "Starting Ollama on port $PORT..."
  OLLAMA_HOST=localhost:$PORT ollama serve > "ollama_$PORT.log" 2>&1 &
  echo "Ollama on port $PORT running in background (log: ollama_$PORT.log)"
}

# Start both instances
start_ollama_instance $PORT1
start_ollama_instance $PORT2

echo "Both Ollama instances launched."