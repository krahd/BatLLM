"""Validate BatLLM's maintained documentation without network access."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
STATUS_TIMESTAMP = re.compile(r"^Last updated: \d{4}-\d{2}-\d{2} \d{2}:\d{2}$")
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
HTML_REFERENCE = re.compile(r"(?:href|src)=\"([^\"]+)\"")

REQUIRED = (
    "README.md",
    "STATUS.md",
    "SECURITY.md",
    "docs/README.md",
    "docs/USER_GUIDE.md",
    "docs/FAQ.md",
    "docs/CONTRIBUTING.md",
    "docs/CHANGELOG.md",
    "docs/ROADMAP.md",
    "docs/RELEASE_CRITERIA_1_0.md",
    "docs/FIRST_RUN_RELEASE_CHECKLIST.md",
    "docs/STATE_AND_INSTALLATION.md",
    "docs/MAINTAINER_AUDIT_CHECKLIST.md",
    "research/urucon2026/README.md",
)

PROHIBITED = (
    "PR_BODY.md",
    "PR_TITLE.txt",
    "batllm-audit-pr.patch",
    "batllm-audit-pr-overlay.zip",
    "batllm-pr-implementation",
    "scripts/apply_audit_pr.sh",
    ".github/DOCS_AUDIT_SNAPSHOT",
    ".github/workflows/docs-audit-snapshot.yml",
)

CANONICAL_PROSE = (
    "README.md",
    "STATUS.md",
    "docs/README.md",
    "docs/USER_GUIDE.md",
    "docs/FAQ.md",
    "docs/CONTRIBUTING.md",
    "docs/ROADMAP.md",
    "docs/RELEASE_CRITERIA_1_0.md",
    "docs/FIRST_RUN_RELEASE_CHECKLIST.md",
    "docs/STATE_AND_INSTALLATION.md",
    "docs/MAINTAINER_AUDIT_CHECKLIST.md",
    "research/urucon2026/README.md",
)

STALE_PATTERNS = {
    "run_tests.sh": "removed Unix test wrapper",
    "complete non-live BatLLM tests, and every research experiment on Linux": (
        "obsolete URUCON workflow description"
    ),
    "docs/README.md`: canonical project overview": "obsolete documentation ownership",
}


def local_target(source: Path, raw_target: str) -> Path | None:
    """Resolve a local Markdown/HTML reference or return None for external links."""
    target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
    if not target or target.startswith(("#", "http://", "https://", "mailto:", "data:")):
        return None
    decoded = unquote(target.split("#", 1)[0])
    if not decoded:
        return None
    return (source.parent / decoded).resolve()


def markdown_files() -> list[Path]:
    """Return maintained Markdown files, excluding generated API documentation."""
    files: list[Path] = []
    for path in ROOT.rglob("*.md"):
        relative = path.relative_to(ROOT)
        if relative.parts[:2] == ("docs", "code"):
            continue
        files.append(path)
    return sorted(files)


def main() -> int:
    """Run all documentation checks and return a shell-friendly status."""
    errors: list[str] = []

    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required documentation: {relative}")

    for relative in PROHIBITED:
        if (ROOT / relative).exists():
            errors.append(f"obsolete or temporary artefact is tracked: {relative}")

    status_path = ROOT / "STATUS.md"
    if status_path.is_file():
        lines = status_path.read_text(encoding="utf-8").splitlines()
        timestamp_lines = [line for line in lines if line.startswith("Last updated:")]
        if len(timestamp_lines) != 2:
            errors.append("STATUS.md must contain exactly two Last updated lines")
        elif timestamp_lines[0] != timestamp_lines[1]:
            errors.append("STATUS.md top and bottom timestamps do not match")
        elif not STATUS_TIMESTAMP.fullmatch(timestamp_lines[0]):
            errors.append("STATUS.md timestamp format is invalid")
        if not lines or lines[-1] != (timestamp_lines[-1] if timestamp_lines else ""):
            errors.append("STATUS.md must end with the repeated Last updated line")

    root_resolved = ROOT.resolve()
    for path in markdown_files():
        text = path.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK.finditer(text):
            target = local_target(path, match.group(1))
            if target is None:
                continue
            try:
                target.relative_to(root_resolved)
            except ValueError:
                errors.append(
                    f"{path.relative_to(ROOT)}:{text.count(chr(10), 0, match.start()) + 1}: "
                    "local link escapes repository"
                )
                continue
            if not target.exists():
                errors.append(
                    f"{path.relative_to(ROOT)}:{text.count(chr(10), 0, match.start()) + 1}: "
                    f"missing local link target {match.group(1)!r}"
                )

    index_path = ROOT / "docs" / "index.html"
    if index_path.is_file():
        text = index_path.read_text(encoding="utf-8")
        for match in HTML_REFERENCE.finditer(text):
            target = local_target(index_path, match.group(1))
            if target is not None and not target.exists():
                errors.append(
                    f"docs/index.html:{text.count(chr(10), 0, match.start()) + 1}: "
                    f"missing local reference {match.group(1)!r}"
                )

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    for relative in ("README.md", "STATUS.md"):
        path = ROOT / relative
        if path.is_file() and version not in path.read_text(encoding="utf-8"):
            errors.append(f"{relative} does not mention repository version {version}")

    for relative in CANONICAL_PROSE:
        path = ROOT / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for pattern, reason in STALE_PATTERNS.items():
            if pattern in text:
                errors.append(f"{relative} contains {reason}: {pattern!r}")

    if errors:
        print("Documentation validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Documentation validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
