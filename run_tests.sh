#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-core}"
exec python3 run_tests.py "${MODE}"
