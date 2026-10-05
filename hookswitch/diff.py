"""Diff utilities for hookswitch."""

import difflib


def get_diff(old, new):
    """Return a unified diff string between two contents.

    Args:
        old: Original content (string).
        new: New content (string).

    Returns:
        A unified diff string. Empty when contents are identical.
    """
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    diff = difflib.unified_diff(old_lines, new_lines)
    return "".join(diff)