"""hookswitch list and status."""

import json

from tests.conftest import STASH_TEXT


def test_list_shows_every_server_with_state(project, hs):
    code, out, _ = hs("list")
    assert code == 0
    lines = out.splitlines()
    assert lines[0].split() == ["NAME", "STATE"]
    assert lines[1].split() == ["github", "on"]
    assert lines[2].split() == ["postgres", "on"]
    assert lines[3].split() == ["puppeteer", "off"]
    assert "2 of 3 enabled (mcp.json)" in out


def test_list_json(project, hs):
    code, out, _ = hs("list", "--json")
    payload = json.loads(out)
    assert code == 0
    assert payload["format"] == "flag"
    assert payload["servers"][2] == {"name": "puppeteer", "enabled": False}


def test_list_reads_stash_layout_and_reports_parked_servers(project, hs):
    (project / "mcp.json").write_text(STASH_TEXT, encoding="utf-8")
    hs("disable", "postgres")
    code, out, _ = hs("list")
    assert code == 0
    assert "github" in out and "on" in out
    assert [ln.split() for ln in out.splitlines()[1:3]] == [["github", "on"], ["postgres", "off"]]


def test_list_with_explicit_config_path(project, hs):
    other = project / "other.json"
    other.write_text('{"servers": {"solo": {"enabled": true}}}', encoding="utf-8")
    code, out, _ = hs("list", "--config", str(other))
    assert code == 0
    assert "solo" in out and "github" not in out


def test_list_empty_config(project, hs):
    (project / "mcp.json").write_text('{"servers": {}}', encoding="utf-8")
    code, out, _ = hs("list")
    assert code == 0
    assert "no servers in mcp.json" in out


def test_list_invalid_json_exits_one_with_message(project, hs):
    (project / "mcp.json").write_text("{nope", encoding="utf-8")
    code, out, err = hs("list")
    assert code == 1
    assert out == ""
    assert "not valid JSON" in err


def test_explicit_missing_config_is_an_error_and_not_created(project, hs):
    code, _, err = hs("list", "--config", "typo.json")
    assert code == 1
    assert "config file not found: typo.json" in err
    assert not (project / "typo.json").exists()


def test_env_var_selects_config(project, hs, monkeypatch):
    other = project / "env.json"
    other.write_text('{"servers": {"from_env": {"enabled": true}}}', encoding="utf-8")
    monkeypatch.setenv("HOOKSWITCH_CONFIG", str(other))
    _, out, _ = hs("list")
    assert "from_env" in out
