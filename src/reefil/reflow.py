from __future__ import annotations

import io
import re
import textwrap
import tokenize

_SENTENCE_END = re.compile(r"[.!?]\s*$")
_PARAGRAPH_END = re.compile(r":\s*$")
_SENTENCE_START = re.compile(r"^#\s+[A-Z@]")
_LIST_ITEM = re.compile(r"^#\s+(?:[-*+]\s|\d+[.)]\s)")
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
        if _SENTENCE_END.search(line) or _PARAGRAPH_END.search(line):
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


def reflow(source: str, line_length: int) -> str:
    lines = source.split("\n")
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
        for rewrap, chunk in _split_paragraphs(run):
            width = max(line_length - col - 2, 20)
            comments = _wrap(chunk, width) if rewrap else chunk
            out.extend(indent + c for c in comments)
    return "\n".join(out)
