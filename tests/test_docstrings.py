from textwrap import dedent

from reefil import reflow


def refill(source: str, line_length: int = 60) -> str:
    return reflow(source, line_length=line_length, docstrings=True)


def test_off_by_default():
    source = dedent('''\
        def f():
            """Summary.

            A body wrapped
            far too early.
            """
        ''')
    assert reflow(source, line_length=88) == source


def test_joins_a_body_paragraph_broken_mid_sentence():
    source = dedent('''\
        def f():
            """Summary.

            A body wrapped
            far too early.
            """
        ''')
    assert refill(source) == dedent('''\
        def f():
            """Summary.

            A body wrapped far too early.
            """
        ''')


def test_splits_a_body_paragraph_past_the_limit():
    source = dedent('''\
        def f():
            """Summary.

            This paragraph is one long line that runs well past the limit set for it.
            """
        ''')
    assert refill(source, line_length=40) == dedent('''\
        def f():
            """Summary.

            This paragraph is one long line that
            runs well past the limit set for it.
            """
        ''')


def test_leaves_the_summary_alone_even_when_it_overflows():
    source = dedent('''\
        def f():
            """A very long summary line that runs on and on well past the limit.

            Body.
            """
        ''')
    assert refill(source, line_length=40) == source


def test_leaves_one_line_docstrings_alone():
    source = 'def f():\n    """A one line docstring that is far longer than the limit."""\n'
    assert refill(source, line_length=30) == source


def test_leaves_a_body_that_runs_on_from_the_summary_alone():
    source = dedent('''\
        def f():
            """Summary that
            continues here.
            """
        ''')
    assert refill(source) == source


def test_leaves_closing_quotes_on_the_text_line_alone():
    source = dedent('''\
        def f():
            """Summary.

            A body wrapped
            far too early."""
        ''')
    assert refill(source) == source


def test_stops_at_a_google_section():
    source = dedent('''\
        def f(x):
            """Summary.

            A body wrapped
            far too early.

            Args:
                x: an argument wrapped
                    far too early.

            Returns:
                A value wrapped
                far too early.
            """
        ''')
    assert refill(source) == dedent('''\
        def f(x):
            """Summary.

            A body wrapped far too early.

            Args:
                x: an argument wrapped
                    far too early.

            Returns:
                A value wrapped
                far too early.
            """
        ''')


def test_stops_at_a_numpy_section():
    source = dedent('''\
        def f(x):
            """Summary.

            Parameters
            ----------
            x : int
                An argument wrapped
                far too early.
            """
        ''')
    assert refill(source) == source


def test_stops_at_sphinx_fields_directives_and_doctests():
    for stop in (":param x: wrapped\n    far too early.", ".. note:: wrapped\n    early.", ">>> f()"):
        source = dedent('''\
            def f(x):
                """Summary.

                {stop}

                Trailing prose wrapped
                far too early.
                """
            ''').format(stop=stop)
        assert refill(source) == source


def test_skips_indented_and_literal_blocks():
    source = dedent('''\
        def f():
            """Summary.

            Some example follows::

                code that must
                not be joined

            And a table:
              a  b
              c  d
            """
        ''')
    assert refill(source) == source


def test_keeps_list_items_apart():
    source = dedent('''\
        def f():
            """Summary.

            - first item
            - second item
            1. numbered
            2. numbered
            """
        ''')
    assert refill(source) == source


def test_respects_the_sentence_rules_and_greedy():
    source = dedent('''\
        def f():
            """Summary.

            First sentence ends here.
            Second sentence follows.
            """
        ''')
    assert refill(source) == source
    assert reflow(source, line_length=60, greedy=True, docstrings=True) == dedent('''\
        def f():
            """Summary.

            First sentence ends here. Second sentence follows.
            """
        ''')


def test_module_class_and_nested_docstrings():
    source = dedent('''\
        """Module.

        Module body wrapped
        early.
        """


        class C:
            """Class.

            Class body wrapped
            early.
            """

            async def m(self):
                """Method.

                Method body wrapped
                early.
                """
        ''')
    assert refill(source) == dedent('''\
        """Module.

        Module body wrapped early.
        """


        class C:
            """Class.

            Class body wrapped early.
            """

            async def m(self):
                """Method.

                Method body wrapped early.
                """
        ''')


def test_ignores_single_quoted_and_raw_docstrings():
    for quotes in ("'''", 'r"""'):
        source = dedent("""\
            def f():
                {q}Summary.

                A body wrapped
                far too early.
                {c}
            """).format(q=quotes, c=quotes[-3:])
        assert refill(source) == source


def test_ignores_ordinary_strings():
    source = dedent('''\
        def f():
            x = 1
            """Not a docstring, wrapped
            far too early.
            """
        ''')
    assert refill(source) == source


def test_leaves_files_that_do_not_parse_alone():
    source = 'def f(:\n    """Summary.\n\n    a\n    b\n    """\n'
    assert refill(source) == source


def test_preserves_crlf():
    source = 'def f():\r\n    """Summary.\r\n\r\n    a wrapped\r\n    early.\r\n    """\r\n'
    assert refill(source) == 'def f():\r\n    """Summary.\r\n\r\n    a wrapped early.\r\n    """\r\n'
