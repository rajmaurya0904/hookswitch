"""Tests for hookswitch.diff."""

from hookswitch.diff import get_diff


def test_get_diff_returns_empty_when_identical():
    content = "hello world\n"
    assert get_diff(content, content) == ""


def test_get_diff_returns_non_empty_when_different():
    old = "hello world\n"
    new = "hello world\nsecond line\n"
    diff = get_diff(old, new)
    assert diff != ""
    # Check that it's a unified diff
    assert diff.startswith("---")
    assert "+++" in diff
    assert "+second line" in diff


def test_get_diff_handles_multiline_changes():
    old = "line1\nline2\nline3\n"
    new = "line1\nmodified line2\nline3\n"
    diff = get_diff(old, new)
    assert diff != ""
    assert "-line2" in diff
    assert "+modified line2" in diff