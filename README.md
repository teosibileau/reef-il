# reef-il

Refill prose in Python source to the configured line length: full-line `#`
comments, and with `--docstrings` the body paragraphs of docstrings. A
pre-commit hook for the gap ruff leaves open: E501 flags lines that run past
the limit, but nothing flags prose wrapped well short of it.

## Install

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/teosibileau/reef-il
    rev: v0.1.0
    hooks:
      - id: reef-il
```

Place it before the ruff hooks so E501 sees the refilled result. The line
length comes from `[tool.ruff] line-length` in the nearest `pyproject.toml`,
then `[tool.black]`, then 88. Pass `args: [--line-length, "120"]` to override.

The command also runs on its own:

```sh
reef-il src/**/*.py          # rewrite, exit 1 if anything changed
reef-il --check src/**/*.py  # report only
```

## What it does

Consecutive full-line comments with the same indentation form a paragraph.
Each paragraph is rewrapped to the line length, so a comment broken earlier
than necessary is joined and one that runs past the limit is split.

Before, in a repo set to 120 columns:

```python
# orig_iat was the original issue time at refresh; simplejwt has iat
# per token, but legacy consumers may look for orig_iat specifically.
```

After:

```python
# orig_iat was the original issue time at refresh; simplejwt has iat per token, but legacy consumers may look
# for orig_iat specifically.
```

### Two join rules

By default a line is joined to the next only when the break is mid-sentence:
the line does not end in `.`, `!` or `?`, and the next line does not start
with a capital letter or `@`. One-thought-per-line notes survive:

```python
# Create the deactivated periodic task
# Activate locally/staging/prod as required and remove from crontab on server
```

The cost is a missed join where a sentence happens to end exactly at the old
wrap. `--greedy` drops the sentence rules and joins every adjacent line that
fits, the way fill-paragraph does in an editor.

### What it never touches

- Inline comments after code, and `#` inside strings. Comments are found with
  the tokenizer.
- Shebangs, coding lines, `#:` attribute docs, and bare `#`.
- Suppression directives: `noqa`, `type:`, `fmt:`, `pragma`, `ruff:`,
  `isort:`, `pylint:`, `pyright:`, `mypy:`.
- Banners such as `# ----` and `# -- title ----`.
- List items, `TODO`/`FIXME`/`NOTE` markers, and comments indented deeper
  than their paragraph, such as code samples.

A line ending in `:` closes its paragraph. Files that fail to tokenize are
left unchanged, and CRLF line endings are preserved.

### Docstrings

`--docstrings` (pass it as `args: [--docstrings]` in the hook) also rewraps
the plain prose paragraphs of docstrings, under the same join rules. It is
deliberately narrow:

- Only `"""` docstrings that span several lines with the closing quotes on
  their own line. One-liners, `'''` and raw strings are skipped.
- The summary line is never touched, even when it overflows.
- Rewrapping stops at the first section header (`Args:`, `Returns:`, a NumPy
  underlined header), Sphinx field (`:param x:`), directive (`.. note::`) or
  doctest (`>>>`). Everything from there on is left as it is.
- Paragraphs indented deeper than the docstring, such as code after `::`,
  tables and continuation lines, are left alone.

Treat it as experimental. Docstrings carry far more structure than comments,
and the rules above are heuristics, not a parser for any docstring style.
Review the diff the first time you run it on a codebase, and expect the
description under `Args:` and friends to stay as it is until section-aware
wrapping lands.

## Development

```sh
uv sync
uv run pytest
pre-commit run --all-files
```

## Releasing

Bump `version` in `pyproject.toml`, merge to `main`, then tag and push:

```sh
git tag v0.2.0 && git push origin v0.2.0
```

The release workflow checks the tag against the version, builds and smoke
tests the wheel, publishes to PyPI through trusted publishing, and creates
the GitHub release with the artifacts attached.
