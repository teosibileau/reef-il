from __future__ import annotations

import io
import re
import textwrap
import tokenize

_SENTENCE_END = re.compile(r"[.!?]\s*$")
_PARAGRAPH_END = re.compile(r":\s*$")
_SENTENCE_START = re.compile(r"^#\s+[A-Z@]")
_LIST_ITEM = re.compile(r"^#\s+(?:[-*+]\s|\d+[.)]\s)")
_MARKER = re.compile(r"^#\s+(?:TODO|FIXME|NOTE|XXX|HACK|BUG)\b")
_BANNER = re.compile(r"^#\s*(?:[-=#*~]{2,}(?:\s|$)|.*[-=#*~]{4,}\s*$)")
_DIRECTIVE = re.compile(
    r"^#\s*(?:noqa|type:|fmt:|isort:|ruff:|pragma|pylint:|pyright:|mypy:|nosec|"
    r"pytype:|-\*-)"
)


def _comment_rows(source: str) -> dict[int, int]:
    """1-based row -> column of every comment with only whitespace before it."""
    rows = {}
    try:
        for tok in tokenize.generate_tokens(io.StringIO(source).readline):
            if tok.type == tokenize.COMMENT and not tok.line[: tok.start[1]].strip():
                rows[tok.start[0]] = tok.start[1]
    except (tokenize.TokenError, SyntaxError):
        return {}
    return rows


def _is_prose(line: str) -> bool:
    """Whether a comment line is text that may be rewrapped."""
    if not line.startswith("# "):
        return False  # "#", "#!", "#:", "#####"
    if _BANNER.match(line) or _DIRECTIVE.match(line):
        return False
    if line.startswith("#  "):
        return False  # indented relative to the paragraph: code sample or table
    return bool(re.search(r"[A-Za-z]", line))


def _starts_paragraph(line: str, greedy: bool) -> bool:
    if _LIST_ITEM.match(line) or _MARKER.match(line):
        return True
    return not greedy and bool(_SENTENCE_START.match(line))


def _ends_paragraph(line: str, greedy: bool) -> bool:
    if _PARAGRAPH_END.search(line):
        return True
    return not greedy and bool(_SENTENCE_END.search(line))


def _split_paragraphs(
    run: list[str], greedy: bool = False
) -> list[tuple[bool, list[str]]]:
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
        if _starts_paragraph(line, greedy):
            close()
        current.append(line)
        if _ends_paragraph(line, greedy):
            close()
    close()
    return chunks


def _wrap(paragraph: list[str], width: int) -> list[str]:
    text = " ".join(line[2:].strip() for line in paragraph)
    return [
        "# " + w
        for w in textwrap.wrap(
            text,
            width=width,
            break_long_words=False,
            break_on_hyphens=False,
        )
    ]


def reflow(source: str, line_length: int, greedy: bool = False) -> str:
    """Return ``source`` with its full-line comment paragraphs rewrapped.

    By default a line joins the next only when the break is mid-sentence.
    With ``greedy`` every adjacent prose line that fits is joined.
    """
    newline = "\r\n" if "\r\n" in source else "\n"
    lines = source.split(newline)
    rows = _comment_rows(source)
    out: list[str] = []
    i = 0
    while i < len(lines):
        if i + 1 not in rows:
            out.append(lines[i])
            i += 1
            continue
        col = rows[i + 1]
        indent = lines[i][:col]
        run = []
        while rows.get(i + 1) == col:
            run.append(lines[i][col:])
            i += 1
        for rewrap, chunk in _split_paragraphs(run, greedy):
            width = max(line_length - col - 2, 20)
            comments = _wrap(chunk, width) if rewrap else chunk
            out.extend(indent + c for c in comments)
    return newline.join(out)
