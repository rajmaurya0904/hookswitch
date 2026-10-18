"""The config layouts hookswitch understands, and how each one represents "off".

MCP clients do not agree on a way to disable a server, so hookswitch supports
three layouts and picks one from the shape of the file:

``flag``
    ``{"servers": {"name": {"enabled": true}}}``. Every server stays in the
    file and carries an ``enabled`` boolean. This is hookswitch's own layout.

``stash``
    ``{"mcpServers": {"name": {...}}}`` as used by ``.mcp.json`` and Claude
    Desktop. Those files have no on/off switch, so a disabled server is moved,
    unchanged, into a top-level ``hookswitchDisabled`` object and moved back
    when it is enabled again. Nothing is lost.

``settings``
    A Claude Code settings file with ``enabledMcpjsonServers`` and
    ``disabledMcpjsonServers`` arrays of server names.
"""

from __future__ import annotations

import copy

from .config import ConfigError

FORMATS = ("flag", "stash", "settings")
STASH_KEY = "hookswitchDisabled"
ENABLED_KEY = "enabledMcpjsonServers"
DISABLED_KEY = "disabledMcpjsonServers"


def detect_format(config: dict) -> str:
    """Return the layout name that best matches *config* (``flag`` when in doubt)."""
    if "mcpServers" in config or STASH_KEY in config:
        return "stash"
    if "servers" in config:
        return "flag"
    if ENABLED_KEY in config or DISABLED_KEY in config:
        return "settings"
    return "flag"


def _resolve(config: dict, fmt: str | None) -> str:
    if fmt is None or fmt == "auto":
        return detect_format(config)
    if fmt not in FORMATS:
        raise ConfigError(f"unknown format {fmt!r}; choose one of {', '.join(FORMATS)}")
    return fmt


def _table(config: dict, key: str) -> dict:
    value = config.get(key, {})
    if not isinstance(value, dict):
        raise ConfigError(f'"{key}" must be an object, got {type(value).__name__}')
    return value


def _names(config: dict, key: str) -> list[str]:
    value = config.get(key, [])
    if not isinstance(value, list) or not all(isinstance(n, str) for n in value):
        raise ConfigError(f'"{key}" must be an array of server names')
    return value


def list_servers(config: dict, fmt: str | None = None) -> list[tuple[str, bool]]:
    """Return ``(name, enabled)`` for every server the config knows about."""
    fmt = _resolve(config, fmt)
    if fmt == "flag":
        out = []
        for name, entry in _table(config, "servers").items():
            if not isinstance(entry, dict):
                raise ConfigError(f'server "{name}" must be an object')
            enabled = entry.get("enabled", True)
            if not isinstance(enabled, bool):
                raise ConfigError(f'server "{name}": "enabled" must be true or false')
            out.append((name, enabled))
        return out
    if fmt == "stash":
        live = [(name, True) for name in _table(config, "mcpServers")]
        parked = [(name, False) for name in _table(config, STASH_KEY)]
        return live + parked
    disabled = set(_names(config, DISABLED_KEY))
    names = list(dict.fromkeys(_names(config, ENABLED_KEY) + _names(config, DISABLED_KEY)))
    return [(name, name not in disabled) for name in names]


def has_server(config: dict, name: str, fmt: str | None = None) -> bool:
    """True if *name* can be toggled in this config."""
    fmt = _resolve(config, fmt)
    if fmt == "settings":
        return True
    return name in dict(list_servers(config, fmt))


def set_enabled(config: dict, name: str, enabled: bool, fmt: str | None = None) -> dict:
    """Return a copy of *config* with *name* switched on or off.

    Setting a server to the state it is already in returns an equal copy. An
    unknown server raises ``KeyError`` (the ``settings`` layout accepts any name,
    since the arrays are not a registry of servers).
    """
    fmt = _resolve(config, fmt)
    new = copy.deepcopy(config)
    if fmt == "flag":
        servers = new.setdefault("servers", {})
        if name not in servers:
            raise KeyError(name)
        if not isinstance(servers[name], dict):
            raise ConfigError(f'server "{name}" must be an object')
        servers[name]["enabled"] = enabled
    elif fmt == "stash":
        live = new.setdefault("mcpServers", {})
        parked = _table(new, STASH_KEY)
        if name not in live and name not in parked:
            raise KeyError(name)
        if enabled and name in parked:
            live[name] = parked.pop(name)
        elif not enabled and name in live:
            parked = new.setdefault(STASH_KEY, {})
            parked[name] = live.pop(name)
        if STASH_KEY in new and not new[STASH_KEY]:
            del new[STASH_KEY]
    else:
        on = _names(new, ENABLED_KEY)
        off = _names(new, DISABLED_KEY)
        if enabled:
            on = on if name in on else [*on, name]
            off = [n for n in off if n != name]
        else:
            off = off if name in off else [*off, name]
            on = [n for n in on if n != name]
        for key, names in ((ENABLED_KEY, on), (DISABLED_KEY, off)):
            if names or key in new:
                new[key] = names
    return new
