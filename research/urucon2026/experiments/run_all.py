"""Run every deterministic URUCON experiment in dependency order."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def main() -> int:
    for script in (
        "generate_corpus.py",
        "differential_semantics.py",
        "inject_faults.py",
        "serialization_controls.py",
        "measure_overhead.py",
        "render_results.py",
    ):
        process = subprocess.run(
            [sys.executable, str(HERE / script)],
            cwd=HERE,
            check=False,
        )
        if process.returncode:
            return process.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
