"""Diff utilities for hookswitch."""

from __future__ import annotations

import difflib

RED = "\x1b[31m"
GREEN = "\x1b[32m"
CYAN = "\x1b[36m"
BOLD = "\x1b[1m"
RESET = "\x1b[0m"
NO_NEWLINE_MARK = chr(92) + " No newline at end of file"


def get_diff(old: str, new: str, fromfile: str = "", tofile: str = "") -> str:
    """Return a unified diff between two texts.

    Args:
        old: Original content.
        new: New content.
        fromfile: Label for the ``---`` header line (for example the file path).
        tofile: Label for the ``+++`` header line.

    Returns:
        A unified diff string, or ``""`` when the texts are identical. A final
        line without a newline is reported as such instead of being glued to
        the next diff line.
    """
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    out: list[str] = []
    for line in difflib.unified_diff(old_lines, new_lines, fromfile=fromfile, tofile=tofile):
        if line.endswith("\n"):
            out.append(line)
        else:
            out.append(f"{line}\n{NO_NEWLINE_MARK}\n")
    return "".join(out)


def colorize(diff: str) -> str:
    """Wrap the lines of a unified diff in ANSI colours (red removals, green additions)."""
    if not diff:
        return diff
    lines = []
    for line in diff.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        tail = line[len(body) :]
        if line.startswith(("---", "+++")):
            lines.append(f"{BOLD}{body}{RESET}{tail}")
        elif line.startswith("@@"):
            lines.append(f"{CYAN}{body}{RESET}{tail}")
        elif line.startswith("+"):
            lines.append(f"{GREEN}{body}{RESET}{tail}")
        elif line.startswith("-"):
            lines.append(f"{RED}{body}{RESET}{tail}")
        else:
            lines.append(line)
    return "".join(lines)
