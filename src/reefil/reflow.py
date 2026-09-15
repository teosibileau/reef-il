from __future__ import annotations

import textwrap


def _is_comment(line: str) -> bool:
    return line.startswith("# ")


def reflow(source: str, line_length: int) -> str:
    lines = source.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        if not _is_comment(lines[i]):
            out.append(lines[i])
            i += 1
            continue
        paragraph = []
        while i < len(lines) and _is_comment(lines[i]):
            paragraph.append(lines[i][2:].strip())
            i += 1
        text = " ".join(paragraph)
        out.extend(
            "# " + w
            for w in textwrap.wrap(
                text,
                width=line_length - 2,
                break_long_words=False,
                break_on_hyphens=False,
            )
        )
    return "\n".join(out)
