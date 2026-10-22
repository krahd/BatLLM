"""Run LXAI Experiment 1 through the strict direct Ollama transport.

This wrapper exists because Modelito 1.4.5's OllamaProvider.summarize() ignores
its settings/options argument. The shared experiment/scoring code remains in
run_experiment.py; only the transport is replaced here.
"""
from __future__ import annotations

import sys

import run_experiment as base
from direct_ollama_client import DirectOllamaChatClient


def main(argv: list[str] | None = None) -> int:
    base.ModelitoChatClient = DirectOllamaChatClient
    return base.main(list(sys.argv[1:] if argv is None else argv))


if __name__ == "__main__":
    raise SystemExit(main())
