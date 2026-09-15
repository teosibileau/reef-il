from textwrap import dedent

from reefil import reflow


def test_joins_lines_broken_mid_sentence():
    source = dedent("""\
        # This comment was wrapped at
        # sixty columns by an old habit.
        x = 1
        """)
    assert reflow(source, line_length=88) == dedent("""\
        # This comment was wrapped at sixty columns by an old habit.
        x = 1
        """)


def test_splits_a_line_longer_than_the_limit():
    source = (
        "# A single comment line that runs on well past the limit "
        "and has to be split.\n"
    )
    assert reflow(source, line_length=40) == dedent("""\
        # A single comment line that runs on
        # well past the limit and has to be
        # split.
        """)
