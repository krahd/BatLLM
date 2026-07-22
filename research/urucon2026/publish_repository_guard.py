#!/usr/bin/env python3
"""Run the repository publisher and preserve an actionable failure report."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import traceback

import publish_repository

ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "research/urucon2026"
REPORT = RESEARCH / "FINAL_PUBLICATION_ERROR.md"


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=ROOT, text=True, check=check, capture_output=True
    )


def preserve_report(content: str) -> None:
    REPORT.write_text(content, encoding="utf-8")
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
        print(content)


def docx_preflight() -> None:
    process = subprocess.run(
        [sys.executable, str(RESEARCH / "paper/build_docx.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode:
        preserve_report(
            "# Final URUCON publication failure\n\n"
            "The editable DOCX build failed before repository packaging.\n\n"
            "## Standard output\n\n```text\n"
            f"{process.stdout}"
            "```\n\n## Standard error\n\n```text\n"
            f"{process.stderr}"
            "```\n"
        )
        raise subprocess.CalledProcessError(
            process.returncode,
            process.args,
            output=process.stdout,
            stderr=process.stderr,
        )


def main() -> int:
    try:
        docx_preflight()
        return publish_repository.main()
    except Exception as exc:  # publication diagnostics must survive the runner
        if not REPORT.exists() or "Standard error" not in REPORT.read_text(
            encoding="utf-8"
        ):
            details = traceback.format_exc()
            preserve_report(
                "# Final URUCON publication failure\n\n"
                f"Exception: `{type(exc).__name__}: {exc}`\n\n"
                "```text\n"
                f"{details}"
                "```\n"
            )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
