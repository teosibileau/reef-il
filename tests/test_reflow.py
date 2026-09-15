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


def test_does_not_join_across_the_end_of_a_sentence():
    source = dedent("""\
        # Create the deactivated periodic task.
        # Activate locally as required.
        """)
    assert reflow(source, line_length=88) == source


def test_does_not_join_when_the_next_line_starts_a_sentence():
    source = dedent("""\
        # Create the deactivated periodic task
        # Activate locally as required
        # @alex: TODO forbid .svg files
        # @alex: TODO upload to S3
        """)
    assert reflow(source, line_length=88) == source


def test_keeps_list_items_on_their_own_lines():
    source = dedent("""\
        # - first item
        # - second item
        # * starred item
        # 1. numbered item
        """)
    assert reflow(source, line_length=88) == source


def test_markers_such_as_todo_start_their_own_paragraph():
    source = dedent("""\
        # the first note ends here
        # TODO: do the thing
        # FIXME: the other thing
        # NOTE: a note
        """)
    assert reflow(source, line_length=88) == source


def test_leaves_banners_alone_and_does_not_mistake_kwargs_for_one():
    source = dedent("""\
        # -- section title -----------------------
        # prose under the banner that
        # continues here
        # ----------------------------------------
        # **kwargs are forwarded and the line
        # continues here
        """)
    assert reflow(source, line_length=88) == dedent("""\
        # -- section title -----------------------
        # prose under the banner that continues here
        # ----------------------------------------
        # **kwargs are forwarded and the line continues here
        """)


def test_leaves_directive_and_header_comments_alone():
    source = dedent("""\
        #!/usr/bin/env python3
        # -*- coding: utf-8 -*-
        # noqa: E501
        # type: ignore
        # fmt: off
        # pragma: no cover
        # ruff: noqa
        #: sphinx attribute doc
        #
        # prose that follows and
        # continues here
        """)
    assert reflow(source, line_length=88) == dedent("""\
        #!/usr/bin/env python3
        # -*- coding: utf-8 -*-
        # noqa: E501
        # type: ignore
        # fmt: off
        # pragma: no cover
        # ruff: noqa
        #: sphinx attribute doc
        #
        # prose that follows and continues here
        """)


def test_leaves_inline_comments_alone():
    source = dedent("""\
        import os  # inline comment that is long enough to look like it wants wrapping
        # a full-line comment that
        # continues here
        x = 1  # short
        # another
        """)
    assert reflow(source, line_length=40) == dedent("""\
        import os  # inline comment that is long enough to look like it wants wrapping
        # a full-line comment that continues
        # here
        x = 1  # short
        # another
        """)


def test_leaves_hashes_inside_strings_alone():
    source = dedent('''\
        TEMPLATE = """
        # not a comment that
        # should be joined
        """
        # a real comment that
        # should be joined
        ''')
    assert reflow(source, line_length=88) == dedent('''\
        TEMPLATE = """
        # not a comment that
        # should be joined
        """
        # a real comment that should be joined
        ''')


def test_keeps_indentation_and_leaves_deeper_indented_lines_alone():
    source = dedent("""\
        def f():
            # an indented comment that
            # continues here
            #     sample = code()
            # and the prose resumes
            return 1
        """)
    assert reflow(source, line_length=88) == dedent("""\
        def f():
            # an indented comment that continues here
            #     sample = code()
            # and the prose resumes
            return 1
        """)


def test_a_line_ending_in_a_colon_closes_its_paragraph():
    source = dedent("""\
        # the options are the following:
        # left, right and center are
        # the choices
        """)
    assert reflow(source, line_length=88) == dedent("""\
        # the options are the following:
        # left, right and center are the choices
        """)


def test_greedy_joins_across_sentence_boundaries_but_not_markers():
    source = dedent("""\
        # Create the deactivated periodic task.
        # Activate locally as required.
        # TODO: still its own paragraph
        # - still a list item
        """)
    assert reflow(source, line_length=88, greedy=True) == dedent("""\
        # Create the deactivated periodic task. Activate locally as required.
        # TODO: still its own paragraph
        # - still a list item
        """)


def test_a_reflowed_file_is_stable_on_a_second_pass():
    source = dedent("""\
        # This comment was wrapped at sixty
        # columns by an old habit. It has two
        # sentences, and a list:
        # - one
        # - two
        #
        # And a second paragraph after a blank
        # comment line.
        """)
    once = reflow(source, line_length=60)
    assert once != source
    assert reflow(once, line_length=60) == once


def test_keeps_crlf_line_endings():
    source = "# a comment that\r\n# continues here\r\nx = 1\r\n"
    expected = "# a comment that continues here\r\nx = 1\r\n"
    assert reflow(source, line_length=88) == expected
