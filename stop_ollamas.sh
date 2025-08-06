#!/bin/bash

# This script stops the Ollama instances running on ports 5001 and 5002.

pkill -f "OLLAMA_HOST=localhost:5001"
pkill -f "OLLAMA_HOST=localhost:5002"