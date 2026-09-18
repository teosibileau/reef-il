"""Rewrap the plain prose paragraphs of docstrings.

Only the safe subset is touched: a triple double-quoted docstring spanning
several lines, whose closing quotes sit alone on the last line. The summary
line is never changed. Body paragraphs are rewrapped only up to the first
section header, field list, directive or doctest, and only when every line
of the paragraph shares the docstring's indentation.
"""

from __future__ import annotations

import ast
import re

from reefil.reflow import split_paragraphs, wrap

_SECTION = re.compile(
    r"^(?:Args|Arguments|Parameters|Other Parameters|Keyword Args|Keyword Arguments|"
    r"Returns|Yields|Receives|Raises|Warns|Attributes|Methods|Examples?|Notes?|"
    r"See Also|References|Todo|Warnings?|Usage):\s*$"
)
_UNDERLINE = re.compile(r"^[-=~^]{3,}\s*$")
_STOP = re.compile(r"^(?::\w|\.\.\s|>>>)")
_LITERAL = re.compile(r"::\s*$")


def _docstring_nodes(tree: ast.Module) -> list[ast.Constant]:
    nodes = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = node.body
        if not body or not isinstance(body[0], ast.Expr):
            continue
        value = body[0].value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            nodes.append(value)
    return nodes


def _prose_blocks(body: list[str], indent: str) -> list[tuple[int, int]]:
    """(start, end) index pairs of body blocks that are plain prose."""
    blocks: list[tuple[int, int]] = []
    i = 0
    after_literal = False
    while i < len(body):
        if not body[i].strip():
            i += 1
            continue
        start = i
        while i < len(body) and body[i].strip():
            i += 1
        lines = body[start:i]
        first = lines[0][len(indent) :] if lines[0].startswith(indent) else ""
        if _SECTION.match(first) or _STOP.match(first):
            break
        if len(lines) > 1 and _UNDERLINE.match(lines[1].strip()):
            break
        aligned = all(
            line.startswith(indent) and not line[len(indent) :][:1].isspace() for line in lines
        )
        if aligned and not after_literal and not any(line.rstrip().endswith("\\") for line in lines):
            blocks.append((start, i))
        after_literal = bool(_LITERAL.search(lines[-1]))
    return blocks


def reflow_docstrings(source: str, line_length: int, greedy: bool = False) -> str:
    """Return ``source`` with the plain prose of its docstrings rewrapped."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return source
    newline = "\r\n" if "\r\n" in source else "\n"
    lines = source.split(newline)
    # Edit from the bottom up so earlier line numbers stay valid.
    nodes = sorted(_docstring_nodes(tree), key=lambda n: n.lineno, reverse=True)
    for node in nodes:
        first, last = node.lineno - 1, node.end_lineno - 1
        if last - first < 2:
            continue  # one line, or body-less: nothing but the summary
        opening = lines[first]
        closing = lines[last]
        if opening[node.col_offset :][:3] != '"""' or '"""' in opening[node.col_offset + 3 :]:
            continue
        if closing.strip() != '"""':
            continue
        indent = closing[: len(closing) - len(closing.lstrip())]
        if lines[first + 1].strip():
            continue  # body runs straight on from the summary: leave it alone
        body = lines[first + 1 : last]
        width = line_length - len(indent)
        for start, end in reversed(_prose_blocks(body, indent)):
            run = [line[len(indent) :] for line in body[start:end]]
            out: list[str] = []
            for texts, chunk in split_paragraphs(run, lambda t: t, greedy):
                out.extend(wrap(texts, width, indent) if texts else [indent + c for c in chunk])
            body[start:end] = out
        lines[first + 1 : last] = body
    return newline.join(lines)
