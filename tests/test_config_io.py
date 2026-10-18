"""Error handling and atomic writes in hookswitch.config."""

import json
import os

import pytest

from hookswitch.config import ConfigError, load_config, save_config


def test_invalid_json_raises_config_error_with_position(tmp_path):
    path = tmp_path / "mcp.json"
    path.write_text('{"servers": {', encoding="utf-8")
    with pytest.raises(ConfigError) as exc:
        load_config(path)
    assert "not valid JSON" in str(exc.value)
    assert "line 1" in str(exc.value)


def test_top_level_array_is_rejected(tmp_path):
    path = tmp_path / "mcp.json"
    path.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(ConfigError, match="top level must be a JSON object"):
        load_config(path)


def test_empty_file_loads_as_empty_dict(tmp_path):
    path = tmp_path / "mcp.json"
    path.write_text("  \n", encoding="utf-8")
    assert load_config(path) == {}


def test_directory_path_raises_config_error(tmp_path):
    with pytest.raises(ConfigError):
        load_config(tmp_path)


def test_save_is_indented_and_ends_with_newline(tmp_path):
    path = tmp_path / "mcp.json"
    save_config({"servers": {"a": {"enabled": True}}}, path)
    text = path.read_text(encoding="utf-8")
    assert text.endswith("}\n")
    assert '\n  "servers"' in text


def test_save_keeps_non_ascii(tmp_path):
    path = tmp_path / "mcp.json"
    save_config({"servers": {"café": {"enabled": True}}}, path)
    assert "café" in path.read_text(encoding="utf-8")


def test_save_leaves_no_temp_files_behind(tmp_path):
    path = tmp_path / "mcp.json"
    save_config({"a": 1}, path)
    save_config({"a": 2}, path)
    assert sorted(os.listdir(tmp_path)) == ["mcp.json"]
    assert json.loads(path.read_text(encoding="utf-8")) == {"a": 2}


def test_failed_save_keeps_old_file(tmp_path):
    path = tmp_path / "mcp.json"
    save_config({"a": 1}, path)

    class Boom:
        pass

    with pytest.raises(TypeError):
        save_config({"a": Boom()}, path)
    assert json.loads(path.read_text(encoding="utf-8")) == {"a": 1}
    assert sorted(os.listdir(tmp_path)) == ["mcp.json"]


def test_render_keeps_four_space_indent_and_missing_newline():
    from hookswitch.config import render_config

    original = '{\n    "servers": {\n        "a": {"enabled": true}\n    }\n}'
    out = render_config({"servers": {"a": {"enabled": False}}}, original)
    assert '\n    "servers"' in out
    assert not out.endswith("\n")


def test_render_keeps_tab_indent():
    from hookswitch.config import render_config

    out = render_config({"a": {"b": 1}}, '{\n\t"a": {"b": 0}\n}\n')
    assert '\n\t"a"' in out
    assert out.endswith("\n")


def test_ensure_config_creates_default_when_missing(tmp_path):
    from hookswitch.config import ensure_config

    path = tmp_path / "sub" / "hookswitch.json"
    config, created = ensure_config(path)
    assert created is True
    assert config == {"servers": {}}
    assert json.loads(path.read_text(encoding="utf-8")) == {"servers": {}}


def test_ensure_config_does_not_touch_existing_file(tmp_path):
    from hookswitch.config import ensure_config

    path = tmp_path / "mcp.json"
    path.write_text('{"servers": {"a": {"enabled": true}}}', encoding="utf-8")
    config, created = ensure_config(path)
    assert created is False
    assert config["servers"]["a"]["enabled"] is True
    assert path.read_text(encoding="utf-8") == '{"servers": {"a": {"enabled": true}}}'
