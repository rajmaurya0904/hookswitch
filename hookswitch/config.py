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


def save_config(data: dict, path: str | Path) -> None:
    """Write a config dict to *path* as indented JSON, atomically."""
    path = Path(path)
    write_text_atomic(json.dumps(data, indent=2, ensure_ascii=False) + "\n", path)


def toggle_server(config: dict, server_name: str, enabled: bool) -> dict:
    """Flip the enabled flag for a server in the config.

    Returns a new config dict with the server's ``enabled`` value set to
    ``enabled``. The input dict is not modified.
    """
    new_config = json.loads(json.dumps(config))
    servers = new_config.setdefault("servers", {})
    if server_name not in servers:
        raise KeyError(server_name)
    servers[server_name]["enabled"] = enabled
    return new_config
