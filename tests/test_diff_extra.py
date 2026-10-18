"""File labels, missing-newline handling and colour for hookswitch.diff."""

from hookswitch.diff import BOLD, CYAN, GREEN, NO_NEWLINE_MARK, RED, RESET, colorize, get_diff


def test_labels_appear_in_headers():
    diff = get_diff("a\n", "b\n", fromfile="mcp.json", tofile="mcp.json (new)")
    assert diff.splitlines()[0] == "--- mcp.json"
    assert diff.splitlines()[1] == "+++ mcp.json (new)"


def test_missing_trailing_newline_is_flagged():
    diff = get_diff("a\nb", "a\nc")
    assert f"-b\n{NO_NEWLINE_MARK}\n" in diff
    assert f"+c\n{NO_NEWLINE_MARK}\n" in diff


def test_every_diff_line_ends_with_newline():
    assert get_diff("x", "y").endswith("\n")


def test_colorize_wraps_additions_removals_and_hunks():
    diff = get_diff("one\ntwo\n", "one\n2\n", fromfile="f", tofile="f")
    coloured = colorize(diff)
    assert f"{RED}-two{RESET}" in coloured
    assert f"{GREEN}+2{RESET}" in coloured
    assert f"{BOLD}--- f{RESET}" in coloured
    assert CYAN in coloured


def test_colorize_leaves_context_lines_plain():
    diff = get_diff("one\ntwo\nthree\n", "one\nTWO\nthree\n")
    assert " one\n" in colorize(diff)


def test_colorize_empty_diff_is_empty():
    assert colorize("") == ""


def test_colorize_strips_back_to_original():
    diff = get_diff("a\nb\n", "a\nc\n", fromfile="x", tofile="y")
    plain = colorize(diff)
    for code in (RED, GREEN, CYAN, BOLD, RESET):
        plain = plain.replace(code, "")
    assert plain == diff
