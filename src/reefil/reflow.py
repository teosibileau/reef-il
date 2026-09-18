from __future__ import annotations

import io
import re
import textwrap
import tokenize
from collections.abc import Callable

_SENTENCE_END = re.compile(r"[.!?]\s*$")
_PARAGRAPH_END = re.compile(r":\s*$")
_SENTENCE_START = re.compile(r"^[A-Z@]")
_LIST_ITEM = re.compile(r"^(?:[-*+]\s|\d+[.)]\s)")
_MARKER = re.compile(r"^(?:TODO|FIXME|NOTE|XXX|HACK|BUG)\b")
_BANNER = re.compile(r"^#\s*(?:[-=#*~]{2,}(?:\s|$)|.*[-=#*~]{4,}\s*$)")
_DIRECTIVE = re.compile(
    r"^#\s*(?:noqa|type:|fmt:|isort:|ruff:|pragma|pylint:|pyright:|mypy:|nosec|"
    r"pytype:|-\*-)"
)

MIN_WIDTH = 20


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


def _comment_text(line: str) -> str | None:
    """The prose of a comment line, or None when the line must not be rewrapped."""
    if not line.startswith("# "):
        return None  # "#", "#!", "#:", "#####"
    if _BANNER.match(line) or _DIRECTIVE.match(line):
        return None
    if line.startswith("#  "):
        return None  # indented relative to the paragraph: code sample or table
    text = line[2:].strip()
    return text if re.search(r"[A-Za-z]", text) else None


def starts_paragraph(text: str, greedy: bool) -> bool:
    if _LIST_ITEM.match(text) or _MARKER.match(text):
        return True
    return not greedy and bool(_SENTENCE_START.match(text))


def ends_paragraph(text: str, greedy: bool) -> bool:
    if _PARAGRAPH_END.search(text):
        return True
    return not greedy and bool(_SENTENCE_END.search(text))


def split_paragraphs(
    run: list[str], text_of: Callable[[str], str | None], greedy: bool = False
) -> list[tuple[list[str] | None, list[str]]]:
    """Split a run of lines into (prose texts or None, original lines) chunks.

    ``text_of`` returns the rewrappable text of a line, or None for a line that must be kept as it
    is. Chunks with texts are paragraphs to rewrap.
    """
    chunks: list[tuple[list[str] | None, list[str]]] = []
    texts: list[str] = []
    lines: list[str] = []

    def close() -> None:
        nonlocal texts, lines
        if lines:
            chunks.append((texts, lines))
            texts, lines = [], []

    for line in run:
        text = text_of(line)
        if text is None:
            close()
            chunks.append((None, [line]))
            continue
        if starts_paragraph(text, greedy):
            close()
        texts.append(text)
        lines.append(line)
        if ends_paragraph(text, greedy):
            close()
    close()
    return chunks


def wrap(texts: list[str], width: int, prefix: str) -> list[str]:
    return [
        prefix + w
        for w in textwrap.wrap(
            " ".join(texts),
            width=max(width, MIN_WIDTH),
            break_long_words=False,
            break_on_hyphens=False,
        )
    ]


def reflow_comments(source: str, line_length: int, greedy: bool = False) -> str:
    """Return ``source`` with its full-line comment paragraphs rewrapped."""
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
        for texts, chunk in split_paragraphs(run, _comment_text, greedy):
            comments = wrap(texts, line_length - col - 2, "# ") if texts else chunk
            out.extend(indent + c for c in comments)
    return newline.join(out)


def reflow(source: str, line_length: int, greedy: bool = False, docstrings: bool = False) -> str:
    """Return ``source`` with its full-line comment paragraphs rewrapped.

    By default a line joins the next only when the break is mid-sentence.
    With ``greedy`` every adjacent prose line that fits is joined. With ``docstrings`` the plain
    prose paragraphs of docstrings are rewrapped too.
    """
    result = reflow_comments(source, line_length, greedy)
    if docstrings:
        from reefil.docstrings import reflow_docstrings

        result = reflow_docstrings(result, line_length, greedy)
    return result
