from __future__ import annotations

import re
import textwrap

_SENTENCE_END = re.compile(r"[.!?]\s*$")
_SENTENCE_START = re.compile(r"^#\s+[A-Z@]")
_LIST_ITEM = re.compile(r"^#\s+(?:[-*+]\s|\d+[.)]\s)")
_BANNER = re.compile(r"^#\s*(?:[-=#*~]{2,}(?:\s|$)|.*[-=#*~]{4,}\s*$)")
_DIRECTIVE = re.compile(
    r"^#\s*(?:noqa|type:|fmt:|isort:|ruff:|pragma|pylint:|pyright:|mypy:|nosec|"
    r"pytype:|-\*-)"
)


def _is_comment(line: str) -> bool:
    return line.startswith("#")


def _is_prose(line: str) -> bool:
    """Whether a comment line is text that may be rewrapped."""
    if not line.startswith("# "):
        return False  # "#", "#!", "#:", "#####"
    if _BANNER.match(line) or _DIRECTIVE.match(line):
        return False
    return bool(re.search(r"[A-Za-z]", line))


def _starts_paragraph(line: str) -> bool:
    return bool(_SENTENCE_START.match(line) or _LIST_ITEM.match(line))


def _split_paragraphs(run: list[str]) -> list[tuple[bool, list[str]]]:
    """Split a run of comment lines into (rewrap?, lines) chunks."""
    chunks: list[tuple[bool, list[str]]] = []
    current: list[str] = []

    def close() -> None:
        nonlocal current
        if current:
            chunks.append((True, current))
            current = []

    for line in run:
        if not _is_prose(line):
            close()
            chunks.append((False, [line]))
            continue
        if _starts_paragraph(line):
            close()
        current.append(line)
        if _SENTENCE_END.search(line):
            close()
    close()
    return chunks


def _wrap(paragraph: list[str], line_length: int) -> list[str]:
    text = " ".join(line[2:].strip() for line in paragraph)
    return [
        "# " + w
        for w in textwrap.wrap(
            text,
            width=line_length - 2,
            break_long_words=False,
            break_on_hyphens=False,
        )
    ]


def reflow(source: str, line_length: int) -> str:
    lines = source.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        if not _is_comment(lines[i]):
            out.append(lines[i])
            i += 1
            continue
        run = []
        while i < len(lines) and _is_comment(lines[i]):
            run.append(lines[i])
            i += 1
        for rewrap, chunk in _split_paragraphs(run):
            out.extend(_wrap(chunk, line_length) if rewrap else chunk)
    return "\n".join(out)
