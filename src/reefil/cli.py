from __future__ import annotations

import argparse
import sys
from pathlib import Path

from reefil.reflow import reflow

DEFAULT_LINE_LENGTH = 88


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="reef-il",
        description="Refill full-line # comments to the configured line length.",
    )
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report files that would change without writing them",
    )
    args = parser.parse_args(argv)

    changed = 0
    for path in args.files:
        source = path.read_text(encoding="utf-8")
        result = reflow(source, DEFAULT_LINE_LENGTH)
        if result == source:
            continue
        changed += 1
        if args.check:
            print(f"would reflow comments in {path}")
        else:
            path.write_text(result, encoding="utf-8")
            print(f"reflowed comments in {path}")
    return 1 if changed else 0


if __name__ == "__main__":
    sys.exit(main())
