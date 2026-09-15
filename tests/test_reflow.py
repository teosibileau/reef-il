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
