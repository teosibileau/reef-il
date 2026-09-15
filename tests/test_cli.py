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
