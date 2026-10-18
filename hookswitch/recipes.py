"""Recipes: named lists of server toggles stored as small YAML or JSON files.

A recipe says which servers should be on and which off. Three spellings are
accepted and may be mixed in one file::

    description: Docs work, no database
    enable: [github]
    disable: [postgres, puppeteer]

    servers:            # same shape as the config itself
      github: true
      postgres: {enabled: false}

    toggles:
      - {server: puppeteer, enabled: false}
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .config import ConfigError

SUFFIXES = (".yaml", ".yml", ".json")

Toggle = tuple[str, bool]


class RecipeError(ConfigError):
    """Raised for a recipe that is missing, unreadable or malformed."""


@dataclass
class Recipe:
    name: str
    path: Path
    description: str = ""
    toggles: list[Toggle] = field(default_factory=list)


def recipe_files(directory: str | Path) -> list[Path]:
    """Return the recipe files in *directory*, sorted by name. Missing directory gives []."""
    directory = Path(directory)
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.iterdir() if p.is_file() and p.suffix in SUFFIXES)


def _server_name(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RecipeError(f"{where}: server names must be non-empty strings, got {value!r}")
    return value.strip()


def _name_list(value: Any, key: str, path: Path) -> list[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        raise RecipeError(f'{path}: "{key}" must be a list of server names')
    return [_server_name(v, f'{path}: "{key}"') for v in value]


def _state(value: Any, where: str) -> bool:
    if isinstance(value, dict):
        value = value.get("enabled", True)
    if not isinstance(value, bool):
        raise RecipeError(f"{where}: expected true/false or {{enabled: true/false}}")
    return value


def parse_recipe(data: Any, path: Path) -> Recipe:
    """Turn parsed YAML/JSON into a :class:`Recipe`, validating as it goes."""
    if not isinstance(data, dict):
        raise RecipeError(f"{path}: a recipe must be a mapping, got {type(data).__name__}")
    known = {"description", "name", "enable", "disable", "servers", "toggles"}
    unknown = sorted(set(data) - known)
    if unknown:
        raise RecipeError(f"{path}: unknown key(s): {', '.join(map(str, unknown))}")

    toggles: list[Toggle] = []
    for name in _name_list(data.get("enable", []), "enable", path):
        toggles.append((name, True))
    for name in _name_list(data.get("disable", []), "disable", path):
        toggles.append((name, False))

    servers = data.get("servers", {})
    if not isinstance(servers, dict):
        raise RecipeError(f'{path}: "servers" must be a mapping of name to true/false')
    for raw, value in servers.items():
        name = _server_name(raw, f'{path}: "servers"')
        toggles.append((name, _state(value, f'{path}: servers.{name}')))

    items = data.get("toggles", [])
    if not isinstance(items, list):
        raise RecipeError(f'{path}: "toggles" must be a list')
    for i, item in enumerate(items):
        where = f"{path}: toggles[{i}]"
        if not isinstance(item, dict) or "server" not in item or "enabled" not in item:
            raise RecipeError(f'{where}: expected {{server: NAME, enabled: true/false}}')
        if not isinstance(item["enabled"], bool):
            raise RecipeError(f'{where}: "enabled" must be true or false')
        toggles.append((_server_name(item["server"], where), item["enabled"]))

    wanted: dict[str, bool] = {}
    for name, enabled in toggles:
        if name in wanted and wanted[name] != enabled:
            raise RecipeError(f'{path}: "{name}" is both enabled and disabled')
        wanted[name] = enabled
    deduped = list(wanted.items())

    description = data.get("description", "")
    if not isinstance(description, str):
        raise RecipeError(f'{path}: "description" must be text')
    return Recipe(name=path.stem, path=path, description=description.strip(), toggles=deduped)


def load_recipe_file(path: str | Path) -> Recipe:
    """Read and validate one recipe file (YAML or JSON, chosen by suffix)."""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RecipeError(f"cannot read recipe {path}: {exc.strerror or exc}") from exc
    try:
        data = json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise RecipeError(f"{path} is not valid {path.suffix.lstrip('.').upper()}: {exc}") from exc
    return parse_recipe(data if data is not None else {}, path)


def load_recipes(directory: str | Path) -> dict[str, list[Toggle]]:
    """Map recipe name (file stem) to its ``[(server, enabled), ...]`` toggles."""
    out: dict[str, list[Toggle]] = {}
    for path in recipe_files(directory):
        recipe = load_recipe_file(path)
        if recipe.name in out:
            raise RecipeError(f"two recipes named {recipe.name!r} in {directory}")
        out[recipe.name] = recipe.toggles
    return out


def find_recipe(name: str, directories: list[Path]) -> Recipe:
    """Locate a recipe by file path or by name in the first directory that has it."""
    direct = Path(name)
    if direct.suffix in SUFFIXES and direct.is_file():
        return load_recipe_file(direct)
    for directory in directories:
        for suffix in SUFFIXES:
            candidate = directory / f"{name}{suffix}"
            if candidate.is_file():
                return load_recipe_file(candidate)
    searched = ", ".join(str(d) for d in directories) or "(no recipe directories)"
    raise RecipeError(f"recipe {name!r} not found (looked in {searched})")
