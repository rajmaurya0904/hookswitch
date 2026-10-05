"""Config loading and saving (JSON)."""

import json
from pathlib import Path


def load_config(path: str | Path) -> dict:
    """Load a JSON config file.

    Returns a default empty config if the file does not exist.
    """
    path = Path(path)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_config(data: dict, path: str | Path) -> None:
    """Write a config dict to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
