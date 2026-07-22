#!/usr/bin/env python3
"""Run the repository publisher and preserve an actionable failure report."""

from __future__ import annotations

from pathlib import Path
import subprocess
import traceback

import publish_repository

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "research/urucon2026/FINAL_PUBLICATION_ERROR.md"


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=ROOT, text=True, check=check, capture_output=True
    )


def main() -> int:
    try:
        return publish_repository.main()
    except Exception as exc:  # publication diagnostics must survive the runner
        details = traceback.format_exc()
        REPORT.write_text(
            "# Final URUCON publication failure\n\n"
            f"Exception: `{type(exc).__name__}: {exc}`\n\n"
            "```text\n"
            f"{details}"
            "```\n",
            encoding="utf-8",
        )
        try:
            git("config", "user.name", "github-actions[bot]")
            git(
                "config",
                "user.email",
                "41898282+github-actions[bot]@users.noreply.github.com",
            )
            git("add", "-f", str(REPORT.relative_to(ROOT)))
            git(
                "commit",
                "-m",
                "audit: preserve URUCON publication failure [skip ci]",
            )
            git("push", "origin", "HEAD:urucon")
        except Exception:
            print(details)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
