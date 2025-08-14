#!/bin/bash


# This script generates a requirements.txt file for the BatLLM project using pipreqs.


python3 -m  pipreqs.pipreqs --force --ignore .git,tests,docs  --use-local ./src > /dev/null 2>&1
mv ./src/requirements.txt .
echo "Requirements.txt:"
echo ""
cat requirements.txt
echo ""
