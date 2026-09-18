from textwrap import dedent

from reefil.cli import main

WRAPPED_EARLY = dedent("""\
    # a comment that
    # continues here
    """)
REFLOWED = "# a comment that continues here\n"


def test_rewrites_a_changed_file_and_exits_1(tmp_path):
    target = tmp_path / "mod.py"
    target.write_text(WRAPPED_EARLY)
    assert main([str(target)]) == 1
    assert target.read_text() == REFLOWED


def test_leaves_a_clean_file_alone_and_exits_0(tmp_path):
    target = tmp_path / "mod.py"
    target.write_text(REFLOWED)
    assert main([str(target)]) == 0
    assert target.read_text() == REFLOWED


def test_check_reports_without_writing(tmp_path):
    target = tmp_path / "mod.py"
    target.write_text(WRAPPED_EARLY)
    assert main(["--check", str(target)]) == 1
    assert target.read_text() == WRAPPED_EARLY


def test_line_length_comes_from_the_nearest_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\nline-length = 30\n")
    target = tmp_path / "pkg" / "mod.py"
    target.parent.mkdir()
    target.write_text("# a comment that runs past thirty columns\n")
    assert main([str(target)]) == 1
    assert target.read_text() == "# a comment that runs past\n# thirty columns\n"


def test_line_length_flag_overrides_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\nline-length = 30\n")
    target = tmp_path / "mod.py"
    target.write_text("# a comment that runs past thirty columns\n")
    assert main(["--line-length", "88", str(target)]) == 0


def test_greedy_flag_joins_across_sentences(tmp_path):
    target = tmp_path / "mod.py"
    target.write_text("# First sentence.\n# Second sentence.\n")
    assert main(["--greedy", str(target)]) == 1
    assert target.read_text() == "# First sentence. Second sentence.\n"


def test_docstrings_flag_opts_in(tmp_path):
    target = tmp_path / "mod.py"
    source = 'def f():\n    """Summary.\n\n    a body wrapped\n    early.\n    """\n'
    target.write_text(source)
    assert main([str(target)]) == 0
    assert main(["--docstrings", str(target)]) == 1
    assert target.read_text() == 'def f():\n    """Summary.\n\n    a body wrapped early.\n    """\n'
