"""render_config keeps the style of the file it rewrites."""

import json

from hookswitch.config import render_config

COMPACT = (
    "{\n"
    '  "servers": {\n'
    '    "github": {"enabled": true},\n'
    '    "pg": {"enabled": true, "args": ["-y", "x"]}\n'
    "  }\n"
    "}\n"
)


def test_unchanged_data_renders_byte_identical_for_compact_file():
    assert render_config(json.loads(COMPACT), COMPACT) == COMPACT


def test_toggle_changes_only_one_line_of_compact_file():
    data = json.loads(COMPACT)
    data["servers"]["pg"]["enabled"] = False
    out = render_config(data, COMPACT)
    before, after = COMPACT.splitlines(), out.splitlines()
    assert len(before) == len(after)
    assert [i for i, (a, b) in enumerate(zip(before, after, strict=True)) if a != b] == [3]


def test_expanded_file_stays_expanded():
    expanded = json.dumps({"servers": {"a": {"enabled": True}}}, indent=2) + "\n"
    assert render_config(json.loads(expanded), expanded) == expanded


def test_new_file_is_expanded_two_space_json():
    out = render_config({"servers": {"a": {"enabled": True}}})
    assert out == json.dumps({"servers": {"a": {"enabled": True}}}, indent=2) + "\n"


def test_long_inline_objects_are_broken_up():
    data = {"servers": {"a": {"enabled": True, "args": ["x" * 80, "y" * 80]}}}
    out = render_config(data, COMPACT)
    assert '"args": [' in out
    assert json.loads(out) == data


def test_empty_containers_render_as_literals():
    data = {"servers": {}, "list": [], "n": None, "f": 1.5}
    out = render_config(data)
    assert json.loads(out) == data
    assert '"servers": {}' in out


def test_rendering_is_always_valid_json_with_unicode():
    data = {"servers": {"café": {"enabled": False, "note": "✓ ok \"quoted\""}}}
    for original in (None, COMPACT, "{\n\t\"a\": 1\n}"):
        assert json.loads(render_config(data, original)) == data
