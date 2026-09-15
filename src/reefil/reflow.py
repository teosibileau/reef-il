from __future__ import annotations

import re
import textwrap

_SENTENCE_END = re.compile(r"[.!?]\s*$")
_SENTENCE_START = re.compile(r"^#\s+[A-Z@]")
_LIST_ITEM = re.compile(r"^#\s+(?:[-*+]\s|\d+[.)]\s)")


def _is_comment(line: str) -> bool:
    return line.startswith("# ")


def _split_paragraphs(run: list[str]) -> list[list[str]]:
    """Split a run of comment lines where a sentence ends or starts."""
    paragraphs: list[list[str]] = []
    current: list[str] = []
    for line in run:
        if current and (_SENTENCE_START.match(line) or _LIST_ITEM.match(line)):
            paragraphs.append(current)
            current = []
        current.append(line)
        if _SENTENCE_END.search(line):
            paragraphs.append(current)
            current = []
    if current:
        paragraphs.append(current)
    return paragraphs


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
        for paragraph in _split_paragraphs(run):
            out.extend(_wrap(paragraph, line_length))
    return "\n".join(out)
