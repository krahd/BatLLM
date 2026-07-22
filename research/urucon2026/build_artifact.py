#!/usr/bin/env python3
"""Create the BatLLM URUCON 2026 research-artefact package."""

from __future__ import annotations

from datetime import datetime
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
RESEARCH = Path(__file__).resolve().parent
ARTIFACT = RESEARCH / "artifact"
PACKAGE = ARTIFACT / "BatLLM_URUCON_2026_Research_Artifact.zip"
MANIFEST = ARTIFACT / "MANIFEST.sha256"
PACKAGE_HASH = ARTIFACT / "PACKAGE.sha256"

AUTHORITATIVE_PAPER = RESEARCH / "paper/BatLLM_URUCON_2026_Paper.docx"
WORD_TEMPLATE = RESEARCH / "paper/conference-template-a4.docx"

CORE_PATHS = [
    RESEARCH,
    ROOT / "src/game/trace_contract.py",
    ROOT / "src/game/session_v3.py",
    ROOT / "src/game/research_runtime.py",
    ROOT / "src/game/trace_verifier.py",
    ROOT / "src/game/replay_engine.py",
    ROOT / "src/tests/test_trace_contract.py",
    ROOT / "src/tests/test_replay_engine.py",
    ROOT / "src/tests/test_game_analyzer.py",
    ROOT / "run_batllm_research.py",
    ROOT / "run_batllm_verify.py",
    ROOT / "requirements.txt",
    ROOT / "CITATION.cff",
    ROOT / "LICENSE",
    ROOT / "STATUS.md",
    ROOT / ".github/workflows/urucon.yml",
]

REMOVED_PAPER_SUFFIXES = {".tex", ".bib", ".log", ".pdf"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def selected_files() -> list[Path]:
    files: set[Path] = set()
    for item in CORE_PATHS:
        if not item.exists():
            continue
        if item.is_file():
            files.add(item)
            continue
        for path in item.rglob("*"):
            if not path.is_file():
                continue
            if path in {PACKAGE, MANIFEST, PACKAGE_HASH}:
                continue
            if any(part in {"__pycache__", ".pytest_cache"} for part in path.parts):
                continue
            if path.suffix in {".aux", ".out"}:
                continue
            if path.parent == RESEARCH / "paper" and path.suffix in REMOVED_PAPER_SUFFIXES:
                continue
            files.add(path)
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix())


def zip_timestamp(path: Path) -> tuple[int, int, int, int, int, int]:
    """Return a stable ZIP timestamp using the source date only."""

    timestamp = datetime.fromtimestamp(path.stat().st_mtime)
    year = max(1980, timestamp.year)
    return (year, timestamp.month, timestamp.day, 0, 0, 0)


def main() -> int:
    ARTIFACT.mkdir(parents=True, exist_ok=True)
    for required in (AUTHORITATIVE_PAPER, WORD_TEMPLATE):
        if not required.exists() or required.stat().st_size == 0:
            raise FileNotFoundError(f"Required Word file is missing: {required}")

    files = selected_files()
    manifest_lines = [
        f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}" for path in files
    ]
    MANIFEST.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

    package_files = files + [MANIFEST]
    with zipfile.ZipFile(
        PACKAGE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for path in sorted(
            package_files, key=lambda item: item.relative_to(ROOT).as_posix()
        ):
            relative = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(relative, date_time=zip_timestamp(path))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (path.stat().st_mode & 0xFFFF) << 16
            archive.writestr(
                info,
                path.read_bytes(),
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            )

    PACKAGE_HASH.write_text(
        f"{sha256(PACKAGE)}  {PACKAGE.name}\n", encoding="utf-8"
    )
    print(f"Packaged {len(files)} files: {PACKAGE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
