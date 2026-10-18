"""Running without a config file creates a valid empty one (default path only)."""

import json


def test_list_in_an_empty_directory_creates_hookswitch_json(tmp_path, monkeypatch, hs):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("HOOKSWITCH_CONFIG", raising=False)
    code, out, err = hs("list")
    assert code == 0
    assert "no servers in hookswitch.json" in out
    assert "created an empty one" in err
    assert json.loads((tmp_path / "hookswitch.json").read_text(encoding="utf-8")) == {
        "servers": {}
    }


def test_status_and_check_also_create_it(tmp_path, monkeypatch, hs):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("HOOKSWITCH_CONFIG", raising=False)
    assert hs("status")[0] == 0
    assert (tmp_path / "hookswitch.json").exists()


def test_toggle_in_an_empty_directory_creates_file_then_reports_unknown_server(
    tmp_path, monkeypatch, hs
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("HOOKSWITCH_CONFIG", raising=False)
    code, _, err = hs("toggle", "github")
    assert code == 1
    assert "unknown server(s): github" in err
    assert (tmp_path / "hookswitch.json").exists()


def test_existing_mcp_json_is_preferred_over_creating_a_new_file(tmp_path, monkeypatch, hs):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("HOOKSWITCH_CONFIG", raising=False)
    (tmp_path / ".mcp.json").write_text('{"mcpServers": {"a": {"command": "x"}}}')
    code, out, _ = hs("list")
    assert code == 0 and "a" in out
    assert not (tmp_path / "hookswitch.json").exists()


def test_dot_mcp_json_wins_over_mcp_json(tmp_path, monkeypatch, hs):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("HOOKSWITCH_CONFIG", raising=False)
    (tmp_path / ".mcp.json").write_text('{"servers": {"dot": {}}}')
    (tmp_path / "mcp.json").write_text('{"servers": {"plain": {}}}')
    assert "dot" in hs("list")[1]


def test_env_var_pointing_at_missing_file_is_an_error(tmp_path, monkeypatch, hs):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOOKSWITCH_CONFIG", str(tmp_path / "absent.json"))
    code, _, err = hs("list")
    assert code == 1
    assert "config file not found" in err
