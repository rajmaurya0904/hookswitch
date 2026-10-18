"""The three config layouts: flag, stash and settings."""

import pytest

from hookswitch.config import ConfigError
from hookswitch.formats import (
    STASH_KEY,
    detect_format,
    has_server,
    list_servers,
    set_enabled,
)

FLAG = {"servers": {"github": {"enabled": True}, "pg": {"enabled": False}, "bare": {}}}
STASH = {
    "mcpServers": {
        "github": {"command": "npx", "args": ["-y", "gh"]},
        "pg": {"command": "uvx", "args": ["pg"], "env": {"DB": "x"}},
    }
}
SETTINGS = {"enabledMcpjsonServers": ["github"], "disabledMcpjsonServers": ["pg"]}


def test_detect_format():
    assert detect_format(FLAG) == "flag"
    assert detect_format(STASH) == "stash"
    assert detect_format(SETTINGS) == "settings"
    assert detect_format({}) == "flag"
    assert detect_format({STASH_KEY: {}}) == "stash"


def test_flag_list_defaults_missing_enabled_to_true():
    assert list_servers(FLAG) == [("github", True), ("pg", False), ("bare", True)]


def test_flag_rejects_non_boolean_enabled():
    with pytest.raises(ConfigError, match="true or false"):
        list_servers({"servers": {"a": {"enabled": "yes"}}})


def test_flag_rejects_non_object_server():
    with pytest.raises(ConfigError, match="must be an object"):
        list_servers({"servers": {"a": 3}})


def test_flag_set_enabled_is_pure():
    out = set_enabled(FLAG, "github", False)
    assert out["servers"]["github"]["enabled"] is False
    assert FLAG["servers"]["github"]["enabled"] is True


def test_flag_unknown_server_is_key_error():
    with pytest.raises(KeyError):
        set_enabled(FLAG, "nope", True)


def test_stash_disable_moves_entry_verbatim():
    out = set_enabled(STASH, "pg", False)
    assert "pg" not in out["mcpServers"]
    assert out[STASH_KEY]["pg"] == STASH["mcpServers"]["pg"]
    assert list_servers(out) == [("github", True), ("pg", False)]


def test_stash_roundtrip_restores_original():
    off = set_enabled(STASH, "pg", False)
    on = set_enabled(off, "pg", True)
    assert on == STASH
    assert STASH_KEY not in on


def test_stash_disable_is_idempotent():
    once = set_enabled(STASH, "pg", False)
    assert set_enabled(once, "pg", False) == once


def test_stash_enable_already_enabled_is_noop():
    assert set_enabled(STASH, "github", True) == STASH


def test_stash_unknown_server_is_key_error():
    with pytest.raises(KeyError):
        set_enabled(STASH, "ghost", False)


def test_stash_keeps_unrelated_keys():
    cfg = {"mcpServers": {"a": {"command": "x"}}, "theme": "dark"}
    assert set_enabled(cfg, "a", False)["theme"] == "dark"


def test_settings_list_and_state():
    assert list_servers(SETTINGS) == [("github", True), ("pg", False)]


def test_settings_disable_moves_name_between_arrays():
    out = set_enabled(SETTINGS, "github", False)
    assert out["enabledMcpjsonServers"] == []
    assert out["disabledMcpjsonServers"] == ["pg", "github"]


def test_settings_enable_unlists_from_disabled():
    out = set_enabled(SETTINGS, "pg", True)
    assert out["disabledMcpjsonServers"] == []
    assert out["enabledMcpjsonServers"] == ["github", "pg"]


def test_settings_is_idempotent_and_keeps_order():
    cfg = {"enabledMcpjsonServers": ["b", "a"], "disabledMcpjsonServers": []}
    assert set_enabled(cfg, "b", True) == cfg


def test_settings_accepts_unknown_names_without_adding_empty_keys():
    out = set_enabled({"theme": "x"}, "new", False, fmt="settings")
    assert out == {"theme": "x", "disabledMcpjsonServers": ["new"]}


def test_settings_rejects_bad_array():
    with pytest.raises(ConfigError, match="array of server names"):
        list_servers({"enabledMcpjsonServers": "github"})


def test_explicit_format_overrides_detection():
    cfg = {"servers": {"a": {"enabled": True}}, "mcpServers": {"b": {}}}
    assert list_servers(cfg, "flag") == [("a", True)]
    assert list_servers(cfg, "stash") == [("b", True)]


def test_unknown_format_name_is_rejected():
    with pytest.raises(ConfigError, match="unknown format"):
        list_servers({}, "toml")


def test_has_server():
    assert has_server(FLAG, "pg")
    assert not has_server(FLAG, "x")
    assert has_server(SETTINGS, "anything")
    assert has_server(set_enabled(STASH, "pg", False), "pg")
