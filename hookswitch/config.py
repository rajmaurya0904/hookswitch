"""Reading and writing the JSON config file that lists MCP servers."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


class ConfigError(Exception):
    """Raised when a config file cannot be read, parsed or understood."""


def load_config(path: str | Path) -> dict:
    """Load a JSON config file.

    A missing file yields an empty dict. A file that is not valid JSON, or whose
    top level is not an object, raises :class:`ConfigError` so a half-written
    file is never silently treated as "no servers".
    """
    path = Path(path)
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"cannot read {path}: {exc.strerror or exc}") from exc
    if not text.strip():
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ConfigError(
            f"{path} is not valid JSON (line {exc.lineno}, column {exc.colno}: {exc.msg})"
        ) from exc
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: top level must be a JSON object, got {type(data).__name__}")
    return data


def write_text_atomic(text: str, path: Path) -> None:
    """Write *text* to *path* through a temp file and ``os.replace``.

    A crash mid-write leaves the old file intact instead of a truncated one.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def detect_indent(text: str) -> str | int:
    """Guess the indentation of a JSON document so a rewrite keeps its style."""
    for line in text.splitlines()[1:]:
        stripped = line.lstrip(" \t")
        if not stripped or stripped == line:
            continue
        lead = line[: len(line) - len(stripped)]
        return "\t" if lead.startswith("\t") else len(lead)
    return 2


def render_config(data: dict, original_text: str | None = None) -> str:
    """Serialise *data* as JSON.

    When *original_text* is given, its indent width and trailing newline are
    reused so that a toggle changes only the lines that really changed.
    """
    if original_text is None or not original_text.strip():
        indent: str | int = 2
        newline = True
    else:
        indent = detect_indent(original_text)
        newline = original_text.endswith("\n")
    out = json.dumps(data, indent=indent, ensure_ascii=False)
    return out + "\n" if newline else out


def save_config(data: dict, path: str | Path, original_text: str | None = None) -> None:
    """Write a config dict to *path* as JSON, atomically.

    Pass the file's previous text as *original_text* to keep its formatting.
    """
    path = Path(path)
    write_text_atomic(render_config(data, original_text), path)


DEFAULT_CONFIG: dict = {"servers": {}}


def ensure_config(path: str | Path) -> tuple[dict, bool]:
    """Load *path*, first creating it with an empty ``servers`` table if it is missing.

    Returns ``(config, created)``.
    """
    path = Path(path)
    if path.exists():
        return load_config(path), False
    config = json.loads(json.dumps(DEFAULT_CONFIG))
    save_config(config, path)
    return config, True


def toggle_server(config: dict, server_name: str, enabled: bool, fmt: str | None = None) -> dict:
    """Return a copy of *config* with *server_name* switched on or off.

    The layout is auto-detected (see :mod:`hookswitch.formats`) unless *fmt* is
    given. The input dict is never modified. An unknown server raises ``KeyError``.
    """
    from .formats import set_enabled

    return set_enabled(config, server_name, enabled, fmt)
