"""Loading and validating recipe files."""

import json

import pytest

from hookswitch.recipes import (
    RecipeError,
    find_recipe,
    load_recipe_file,
    load_recipes,
    recipe_files,
)


def write(path, text):
    path.write_text(text, encoding="utf-8")
    return path


def test_enable_disable_lists(tmp_path):
    p = write(tmp_path / "lean.yaml", "description: Docs\nenable: [github]\ndisable: [pg, pup]\n")
    r = load_recipe_file(p)
    assert r.name == "lean"
    assert r.description == "Docs"
    assert r.toggles == [("github", True), ("pg", False), ("pup", False)]


def test_servers_mapping_accepts_bool_and_enabled_object(tmp_path):
    p = write(tmp_path / "r.yaml", "servers:\n  a: true\n  b: {enabled: false}\n  c: {}\n")
    assert load_recipe_file(p).toggles == [("a", True), ("b", False), ("c", True)]


def test_toggles_list(tmp_path):
    p = write(tmp_path / "r.yml", "toggles:\n  - {server: a, enabled: false}\n")
    assert load_recipe_file(p).toggles == [("a", False)]


def test_json_recipe(tmp_path):
    p = tmp_path / "r.json"
    p.write_text(json.dumps({"enable": ["a"], "disable": ["b"]}), encoding="utf-8")
    assert load_recipe_file(p).toggles == [("a", True), ("b", False)]


def test_single_string_is_accepted_as_one_name(tmp_path):
    p = write(tmp_path / "r.yaml", "disable: pg\n")
    assert load_recipe_file(p).toggles == [("pg", False)]


def test_empty_file_is_an_empty_recipe(tmp_path):
    assert load_recipe_file(write(tmp_path / "r.yaml", "")).toggles == []


def test_conflicting_toggle_is_rejected(tmp_path):
    p = write(tmp_path / "r.yaml", "enable: [a]\ndisable: [a]\n")
    with pytest.raises(RecipeError, match="both enabled and disabled"):
        load_recipe_file(p)


def test_same_toggle_twice_is_deduplicated(tmp_path):
    p = write(tmp_path / "r.yaml", "enable: [a]\nservers: {a: true}\n")
    assert load_recipe_file(p).toggles == [("a", True)]


@pytest.mark.parametrize(
    "text, message",
    [
        ("- a\n- b\n", "must be a mapping"),
        ("enable: 3\n", "list of server names"),
        ("enable: [1]\n", "non-empty strings"),
        ("servers: [a]\n", "mapping of name"),
        ("servers: {a: maybe}\n", "expected true/false"),
        ("toggles: {a: 1}\n", "must be a list"),
        ("toggles: [{server: a}]\n", "expected {server"),
        ("toggles: [{server: a, enabled: 1}]\n", "true or false"),
        ("colour: red\n", "unknown key"),
        ("description: [1]\n", "must be text"),
        ("enable: [a\n", "not valid YAML"),
    ],
)
def test_malformed_recipes(tmp_path, text, message):
    with pytest.raises(RecipeError, match=message):
        load_recipe_file(write(tmp_path / "bad.yaml", text))


def test_bad_json_recipe(tmp_path):
    with pytest.raises(RecipeError, match="not valid JSON"):
        load_recipe_file(write(tmp_path / "bad.json", "{"))


def test_unreadable_recipe(tmp_path):
    with pytest.raises(RecipeError, match="cannot read"):
        load_recipe_file(tmp_path / "nope.yaml")


def test_load_recipes_maps_names_to_toggles(tmp_path):
    write(tmp_path / "a.yaml", "enable: [x]\n")
    write(tmp_path / "b.json", '{"disable": ["y"]}')
    write(tmp_path / "notes.txt", "ignored")
    assert load_recipes(tmp_path) == {"a": [("x", True)], "b": [("y", False)]}


def test_load_recipes_missing_directory_is_empty(tmp_path):
    assert load_recipes(tmp_path / "nowhere") == {}
    assert recipe_files(tmp_path / "nowhere") == []


def test_duplicate_stems_are_an_error(tmp_path):
    write(tmp_path / "a.yaml", "enable: [x]\n")
    write(tmp_path / "a.json", "{}")
    with pytest.raises(RecipeError, match="two recipes named"):
        load_recipes(tmp_path)


def test_find_recipe_by_name_and_by_path(tmp_path):
    d = tmp_path / "recipes"
    d.mkdir()
    write(d / "lean.yml", "disable: [pg]\n")
    assert find_recipe("lean", [d]).toggles == [("pg", False)]
    assert find_recipe(str(d / "lean.yml"), []).name == "lean"


def test_find_recipe_missing_lists_search_dirs(tmp_path):
    with pytest.raises(RecipeError, match="not found") as exc:
        find_recipe("ghost", [tmp_path])
    assert str(tmp_path) in str(exc.value)
