"""Backup utilities for config files."""

import shutil
from datetime import datetime
from pathlib import Path


def backup_file(src: str | Path, keep: int = 3) -> Path:
    """Copy *src* to a timestamped ``<src>.bak.<timestamp>`` file and prune older backups.

    At most ``keep`` backup files (matching ``<src>.bak.*``) are retained.
    Returns the path of the newly created backup file.
    """
    src_path = Path(src)
    if not src_path.exists():
        raise FileNotFoundError(f"Source file not found: {src_path}")

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    backup_name = f"{src_path.name}.bak.{timestamp}"
    backup_path = src_path.parent / backup_name

    shutil.copy2(src_path, backup_path)

    # Prune old backups
    pattern = f"{src_path.name}.bak.*"
    backup_files = list(src_path.parent.glob(pattern))
    # Sort by modification time (oldest first)
    backup_files.sort(key=lambda p: p.stat().st_mtime)
    while len(backup_files) > keep:
        oldest = backup_files.pop(0)
        oldest.unlink()

    return backup_path