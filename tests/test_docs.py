"""The shipped example recipes and hook settings stay valid."""

import json
from pathlib import Path

from hookswitch.recipes import load_recipes

DOCS = Path(__file__).resolve().parent.parent / "docs"


def test_example_recipes_load():
    recipes = load_recipes(DOCS / "recipes")
    assert recipes["lean"] == [("github", True), ("postgres", False), ("puppeteer", False)]
    assert recipes["full"] == [("github", True), ("postgres", True), ("puppeteer", True)]


def test_example_hook_settings_call_the_real_command():
    data = json.loads((DOCS / "example_hook_settings.json").read_text(encoding="utf-8"))
    command = data["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    assert command.startswith("hookswitch run lean")


def test_example_recipes_run_against_a_matching_config(tmp_path, monkeypatch, capsys):
    from hookswitch.cli import main

    monkeypatch.chdir(tmp_path)
    cfg = tmp_path / "mcp.json"
    names = ("github", "postgres", "puppeteer")
    cfg.write_text(
        json.dumps({"servers": {n: {"enabled": True} for n in names}}), encoding="utf-8"
    )
    assert main(["run", str(DOCS / "recipes" / "lean.yaml"), "-c", str(cfg), "-q"]) == 0
    state = {n: v["enabled"] for n, v in json.loads(cfg.read_text())["servers"].items()}
    assert state == {"github": True, "postgres": False, "puppeteer": False}
