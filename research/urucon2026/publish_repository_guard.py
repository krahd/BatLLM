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


def ensure_ieee_csl() -> None:
    """Expose Ubuntu's packaged IEEE CSL at a path used by the builder."""

    accepted = (
        Path(
            "/usr/share/texlive/texmf-dist/tex/latex/"
            "citation-style-language/styles/ieee.csl"
        ),
        Path("/usr/share/pandoc/data/csl/ieee.csl"),
    )
    if any(path.exists() for path in accepted):
        return

    subprocess.run(
        [
            "sudo",
            "apt-get",
            "install",
            "-y",
            "-qq",
            "--no-install-recommends",
            "citation-style-language-styles",
        ],
        cwd=ROOT,
        check=True,
    )
    packaged = Path("/usr/share/citation-style-language/styles/ieee.csl")
    if not packaged.exists():
        raise FileNotFoundError(
            "citation-style-language-styles did not provide ieee.csl"
        )
    target = accepted[1]
    subprocess.run(["sudo", "mkdir", "-p", str(target.parent)], check=True)
    subprocess.run(["sudo", "ln", "-sf", str(packaged), str(target)], check=True)
    if not target.exists():
        raise FileNotFoundError("Could not expose the packaged IEEE CSL to Pandoc")


def docx_preflight() -> None:
    ensure_ieee_csl()
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
