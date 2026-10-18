"""toggle / enable / disable: backup, write, diff."""

from hookswitch.backup import list_backups
from tests.conftest import FLAG_TEXT, STASH_TEXT, enabled_map, read_json


def test_toggle_flips_state_writes_file_and_prints_diff(project, hs):
    code, out, _ = hs("toggle", "github")
    assert code == 0
    assert enabled_map(project / "mcp.json")["github"] is False
    assert "disable github" in out
    assert '-    "github": {"enabled": true},' in out
    assert '+    "github": {"enabled": false},' in out
    assert "--- mcp.json (before)" in out and "+++ mcp.json (after)" in out


def test_toggle_creates_a_backup_with_the_old_content(project, hs):
    _, out, _ = hs("toggle", "github")
    backups = list_backups(project / "mcp.json")
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == FLAG_TEXT
    assert f"backup: {backups[0].name}" in out


def test_toggle_twice_returns_to_the_original_bytes(project, hs):
    hs("toggle", "github")
    hs("toggle", "github")
    assert (project / "mcp.json").read_text(encoding="utf-8") == FLAG_TEXT


def test_toggle_on_forces_state_and_is_a_noop_when_already_on(project, hs):
    code, out, _ = hs("toggle", "github", "--on")
    assert code == 0
    assert "no changes" in out
    assert list_backups(project / "mcp.json") == []
    assert (project / "mcp.json").read_text(encoding="utf-8") == FLAG_TEXT


def test_toggle_off_multiple_servers_in_one_edit(project, hs):
    code, out, _ = hs("toggle", "github", "postgres", "--off")
    assert code == 0
    assert enabled_map(project / "mcp.json") == {
        "github": False,
        "postgres": False,
        "puppeteer": False,
    }
    assert len(list_backups(project / "mcp.json")) == 1


def test_on_and_off_together_is_a_usage_error(project, hs, capsys):
    try:
        hs("toggle", "github", "--on", "--off")
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("expected a usage error")


def test_enable_and_disable_commands(project, hs):
    hs("enable", "puppeteer")
    assert enabled_map(project / "mcp.json")["puppeteer"] is True
    hs("disable", "puppeteer", "postgres")
    assert enabled_map(project / "mcp.json") == {
        "github": True,
        "postgres": False,
        "puppeteer": False,
    }


def test_unknown_server_changes_nothing_and_exits_one(project, hs):
    code, out, err = hs("disable", "github", "ghost")
    assert code == 1
    assert "unknown server(s): ghost" in err
    assert "github, postgres, puppeteer" in err
    assert (project / "mcp.json").read_text(encoding="utf-8") == FLAG_TEXT
    assert list_backups(project / "mcp.json") == []


def test_dry_run_prints_diff_but_writes_nothing(project, hs):
    code, out, _ = hs("disable", "github", "--dry-run")
    assert code == 0
    assert '+    "github": {"enabled": false},' in out
    assert "dry run: nothing written" in out
    assert (project / "mcp.json").read_text(encoding="utf-8") == FLAG_TEXT
    assert list_backups(project / "mcp.json") == []


def test_quiet_prints_nothing_but_still_writes(project, hs):
    code, out, err = hs("disable", "github", "-q")
    assert (code, out, err) == (0, "", "")
    assert enabled_map(project / "mcp.json")["github"] is False


def test_keep_limits_the_number_of_backups(project, hs):
    for _ in range(4):
        hs("toggle", "github", "--keep", "2", "-q")
    assert len(list_backups(project / "mcp.json")) == 2


def test_keep_zero_is_rejected(project, hs):
    try:
        hs("toggle", "github", "--keep", "0")
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("expected a usage error")


def test_unrelated_keys_are_preserved(project, hs):
    (project / "mcp.json").write_text(
        '{\n  "note": "keep me",\n  "servers": {"a": {"enabled": true, "env": {"K": "v"}}}\n}\n',
        encoding="utf-8",
    )
    hs("disable", "a", "-q")
    data = read_json(project / "mcp.json")
    assert data["note"] == "keep me"
    assert data["servers"]["a"] == {"enabled": False, "env": {"K": "v"}}


def test_stash_layout_moves_the_server_out_of_mcpservers(project, hs):
    (project / "mcp.json").write_text(STASH_TEXT, encoding="utf-8")
    code, out, _ = hs("disable", "postgres")
    assert code == 0
    data = read_json(project / "mcp.json")
    assert list(data["mcpServers"]) == ["github"]
    assert data["hookswitchDisabled"]["postgres"] == {"command": "uvx", "args": ["pg"]}
    hs("enable", "postgres", "-q")
    assert read_json(project / "mcp.json")["mcpServers"]["postgres"]["command"] == "uvx"


def test_settings_layout(project, hs):
    path = project / "settings.local.json"
    path.write_text(
        '{\n  "enabledMcpjsonServers": ["github"],\n  "disabledMcpjsonServers": []\n}\n',
        encoding="utf-8",
    )
    code, _, _ = hs("disable", "github", "--config", str(path), "-q")
    assert code == 0
    data = read_json(path)
    assert data == {"enabledMcpjsonServers": [], "disabledMcpjsonServers": ["github"]}


def test_format_flag_overrides_detection(project, hs):
    path = project / "both.json"
    path.write_text(
        '{"servers": {"a": {"enabled": true}}, "mcpServers": {"b": {"command": "x"}}}',
        encoding="utf-8",
    )
    hs("disable", "b", "--config", str(path), "--format", "stash", "-q")
    data = read_json(path)
    assert "b" not in data["mcpServers"]
    assert data["servers"]["a"]["enabled"] is True


def test_directory_as_config_is_reported_not_raised(project, hs):
    (project / "mcp.json").unlink()
    (project / "mcp.json").mkdir()
    code, _, err = hs("list", "--config", "mcp.json")
    assert code == 1
    assert err.startswith("hookswitch:")
