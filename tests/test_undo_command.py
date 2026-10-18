"""undo and backups."""

from hookswitch.backup import list_backups
from tests.conftest import FLAG_TEXT


def test_undo_restores_the_previous_file_exactly(project, hs):
    hs("disable", "github", "postgres", "-q")
    code, out, _ = hs("undo")
    assert code == 0
    assert (project / "mcp.json").read_text(encoding="utf-8") == FLAG_TEXT
    assert "restored mcp.json from mcp.json.bak." in out
    assert list_backups(project / "mcp.json") == []


def test_undo_walks_back_one_step_at_a_time(project, hs):
    hs("disable", "github", "-q")
    hs("disable", "postgres", "-q")
    hs("undo", "-q")
    assert "postgres" in hs("status")[1]
    assert "github" not in hs("status")[1]
    hs("undo", "-q")
    assert (project / "mcp.json").read_text(encoding="utf-8") == FLAG_TEXT


def test_undo_without_backups_is_an_error(project, hs):
    code, _, err = hs("undo")
    assert code == 1
    assert "no backups found" in err


def test_undo_without_config_is_an_error(tmp_path, monkeypatch, hs):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("HOOKSWITCH_CONFIG", raising=False)
    code, _, err = hs("undo")
    assert code == 1
    assert "config file not found" in err


def test_undo_quiet(project, hs):
    hs("disable", "github", "-q")
    code, out, err = hs("undo", "-q")
    assert (code, out, err) == (0, "", "")


def test_backups_command_lists_oldest_first(project, hs):
    hs("disable", "github", "-q")
    hs("disable", "postgres", "-q")
    code, out, _ = hs("backups")
    names = out.split()
    assert code == 0 and len(names) == 2
    assert names == sorted(names)
    assert all(n.startswith("mcp.json.bak.") for n in names)


def test_backups_command_when_none(project, hs):
    code, out, _ = hs("backups")
    assert code == 0
    assert "no backups of mcp.json" in out


def test_disable_then_undo_for_stash_layout_restores_original_text(project, hs):
    from tests.conftest import STASH_TEXT

    (project / "mcp.json").write_text(STASH_TEXT, encoding="utf-8")
    hs("disable", "postgres", "-q")
    hs("undo", "-q")
    assert (project / "mcp.json").read_text(encoding="utf-8") == STASH_TEXT
