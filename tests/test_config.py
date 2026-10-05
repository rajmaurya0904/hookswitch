"""Tests for hookswitch.config."""

import json

from hookswitch.config import load_config, save_config


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