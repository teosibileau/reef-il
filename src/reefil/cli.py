from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from reefil.reflow import reflow

DEFAULT_LINE_LENGTH = 88


def line_length_from_pyproject(start: Path) -> int | None:
    """[tool.ruff] line-length, then [tool.black], from the nearest pyproject."""
    for directory in (start, *start.parents):
        pyproject = directory / "pyproject.toml"
        if not pyproject.is_file():
            continue
        text = pyproject.read_text(encoding="utf-8")
        try:
            import tomllib  # type: ignore[import-not-found]
        except ModuleNotFoundError:  # Python < 3.11
            match = re.search(r"^\s*line-length\s*=\s*(\d+)", text, re.M)
            return int(match.group(1)) if match else None
        tool = tomllib.loads(text).get("tool", {})
        return tool.get("ruff", {}).get("line-length") or tool.get("black", {}).get(
            "line-length"
        )
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="reef-il",
        description="Refill full-line # comments to the configured line length.",
    )
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument(
        "--line-length",
        type=int,
        help="defaults to [tool.ruff] line-length in the nearest pyproject.toml, "
        f"then {DEFAULT_LINE_LENGTH}",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report files that would change without writing them",
    )
    args = parser.parse_args(argv)

    changed = 0
    for path in args.files:
        line_length = (
            args.line_length
            or line_length_from_pyproject(path.resolve().parent)
            or DEFAULT_LINE_LENGTH
        )
        source = path.read_text(encoding="utf-8")
        result = reflow(source, line_length)
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
