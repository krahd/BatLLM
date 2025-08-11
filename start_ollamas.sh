#!/bin/bash
# Starts three instances of Ollama on different ports.

# Set ports
PORT0=5000
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
start_ollama_instance $PORT0    
start_ollama_instance $PORT1
start_ollama_instance $PORT2


# Abusive
echo "Three Ollama instances launched! "
echo "Ports: $PORT0, $PORT1, $PORT2"