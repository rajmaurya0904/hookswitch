"""hookswitch run and recipes."""

import pytest

from hookswitch.backup import list_backups
from tests.conftest import FLAG_TEXT, enabled_map


@pytest.fixture
def recipes(project):
    d = project / ".hookswitch" / "recipes"
    d.mkdir(parents=True)
    (d / "lean.yaml").write_text(
        "description: Docs work, no database\nenable: [puppeteer]\ndisable: [postgres]\n",
        encoding="utf-8",
    )
    (d / "everything.json").write_text(
        '{"enable": ["github", "postgres", "puppeteer"]}', encoding="utf-8"
    )
    return d


def test_run_applies_every_toggle_in_one_edit_with_one_backup(project, recipes, hs):
    code, out, _ = hs("run", "lean")
    assert code == 0
    assert enabled_map(project / "mcp.json") == {
        "github": True,
        "postgres": False,
        "puppeteer": True,
    }
    assert len(list_backups(project / "mcp.json")) == 1
    assert "disable postgres" in out and "enable puppeteer" in out
    assert out.count("--- mcp.json (before)") == 1


def test_run_json_recipe(project, recipes, hs):
    hs("run", "everything", "-q")
    assert all(enabled_map(project / "mcp.json").values())


def test_run_is_idempotent(project, recipes, hs):
    hs("run", "lean", "-q")
    before = (project / "mcp.json").read_text(encoding="utf-8")
    code, out, _ = hs("run", "lean")
    assert code == 0
    assert "no changes" in out
    assert (project / "mcp.json").read_text(encoding="utf-8") == before
    assert len(list_backups(project / "mcp.json")) == 1


def test_run_by_file_path(project, hs):
    path = project / "adhoc.yml"
    path.write_text("disable: [github]\n", encoding="utf-8")
    assert hs("run", str(path), "-q")[0] == 0
    assert enabled_map(project / "mcp.json")["github"] is False


def test_run_with_recipes_dir_option(project, hs):
    other = project / "elsewhere"
    other.mkdir()
    (other / "r.yaml").write_text("disable: [github]\n", encoding="utf-8")
    assert hs("run", "r", "--recipes-dir", str(other), "-q")[0] == 0


def test_run_with_recipes_dir_from_environment(project, hs, monkeypatch):
    other = project / "envrecipes"
    other.mkdir()
    (other / "r.yaml").write_text("disable: [github]\n", encoding="utf-8")
    monkeypatch.setenv("HOOKSWITCH_RECIPES", str(other))
    assert hs("run", "r", "-q")[0] == 0


def test_run_unknown_recipe_exits_one(project, recipes, hs):
    code, _, err = hs("run", "nope")
    assert code == 1
    assert "recipe 'nope' not found" in err


def test_run_recipe_naming_unknown_server_changes_nothing(project, hs):
    (project / "bad.yaml").write_text("disable: [github, ghost]\n", encoding="utf-8")
    code, _, err = hs("run", "bad.yaml")
    assert code == 1
    assert "ghost" in err
    assert (project / "mcp.json").read_text(encoding="utf-8") == FLAG_TEXT


def test_skip_missing_applies_the_rest_and_warns(project, hs):
    (project / "bad.yaml").write_text("disable: [github, ghost]\n", encoding="utf-8")
    code, _, err = hs("run", "bad.yaml", "--skip-missing", "-q")
    assert code == 0
    assert "skipping ghost" in err
    assert enabled_map(project / "mcp.json")["github"] is False


def test_run_malformed_recipe_reports_the_file(project, hs):
    (project / "bad.yaml").write_text("enable: [a]\ndisable: [a]\n", encoding="utf-8")
    code, _, err = hs("run", "bad.yaml")
    assert code == 1
    assert "bad.yaml" in err and "both enabled and disabled" in err


def test_run_empty_recipe_is_an_error(project, hs):
    (project / "empty.yaml").write_text("description: nothing\n", encoding="utf-8")
    code, _, err = hs("run", "empty.yaml")
    assert code == 1
    assert "does not toggle any servers" in err


def test_run_dry_run(project, recipes, hs):
    code, out, _ = hs("run", "lean", "--dry-run")
    assert code == 0
    assert "dry run" in out
    assert (project / "mcp.json").read_text(encoding="utf-8") == FLAG_TEXT


def test_recipes_command_lists_summaries(project, recipes, hs):
    code, out, _ = hs("recipes")
    assert code == 0
    assert "lean" in out and "on: puppeteer; off: postgres" in out
    assert "Docs work, no database" in out
    assert "everything" in out


def test_recipes_command_marks_invalid_files(project, recipes, hs):
    (recipes / "broken.yaml").write_text("colour: red\n", encoding="utf-8")
    code, out, _ = hs("recipes")
    assert code == 0
    assert "broken  [invalid]" in out


def test_recipes_command_with_none_found(project, hs):
    code, out, _ = hs("recipes", "--recipes-dir", str(project / "none"))
    assert code == 0
    assert "no recipes found" in out
