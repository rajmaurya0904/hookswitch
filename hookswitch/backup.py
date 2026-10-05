"""Backup utilities for config files."""

import shutil
from pathlib import Path


def backup_file(src: str | Path) -> Path:
    """Copy *src* to a sibling ``<src>.bak`` file.

    Returns the path of the created backup.
    """
    src = Path(src)
    backup = src.parent / (src.name + ".bak")
    shutil.copy2(src, backup)
    return backup
