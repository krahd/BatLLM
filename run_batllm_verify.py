"""Command-line verifier for BatLLM research-session v3 traces."""
# pylint: disable=wrong-import-position

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from game.trace_verifier import (  # noqa: E402
    format_report,
    verify_file,
    write_json_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify a BatLLM research-session v3 trace."
    )
    parser.add_argument("session")
    parser.add_argument("--json", dest="json_path")
    parser.add_argument("--quiet", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = verify_file(args.session)
    if args.json_path:
        write_json_report(report, args.json_path)
    if not args.quiet:
        print(format_report(report))
    return 0 if report.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
