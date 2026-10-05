"""Tests for hookswitch.config."""

import json

from hookswitch.config import load_config, save_config, toggle_server


def test_load_missing_file_returns_empty(tmp_path):
    assert load_config(tmp_path / "nope.json") == {}


def test_save_then_load_roundtrip(tmp_path):
    path = tmp_path / "config.json"
    data = {"servers": {"a": {"enabled": True}}, "version": 1}
    save_config(data, path)
    assert load_config(path) == data


def test_save_creates_parent_dirs(tmp_path):
    path = tmp_path / "nested" / "dir" / "config.json"
    save_config({"x": 1}, path)
    assert path.exists()
    assert json.loads(path.read_text()) == {"x": 1}


def test_toggle_server_flips_enabled():
    config = {"servers": {"a": {"enabled": True}}}
    result = toggle_server(config, "a", False)
    assert result["servers"]["a"]["enabled"] is False


def test_toggle_server_returns_new_dict():
    config = {"servers": {"a": {"enabled": True}}}
    result = toggle_server(config, "a", False)
    assert result is not config
    assert config["servers"]["a"]["enabled"] is True


def test_toggle_server_missing_server_raises():
    config = {"servers": {}}
    try:
        toggle_server(config, "nope", True)
    except KeyError:
        pass
    else:
        raise AssertionError("expected KeyError")