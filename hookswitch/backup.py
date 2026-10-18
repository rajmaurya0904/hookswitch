"""Timestamped backups that sit next to the file they protect."""

from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

DEFAULT_KEEP = 3


def _backup_re(src: Path) -> re.Pattern[str]:
    return re.compile(rf"^{re.escape(src.name)}\.bak\.(\d+)(?:\.(\d+))?$")


def list_backups(src: str | Path) -> list[Path]:
    """Return the backups of *src*, oldest first.

    Only names produced by :func:`backup_file` count, so a hand-made
    ``config.json.bak.old`` is never listed, restored or pruned.
    """
    src_path = Path(src)
    pattern = _backup_re(src_path)
    found: list[tuple[tuple[str, int], Path]] = []
    if not src_path.parent.is_dir():
        return []
    for candidate in src_path.parent.iterdir():
        match = pattern.match(candidate.name)
        if match and candidate.is_file():
            found.append(((match.group(1), int(match.group(2) or 0)), candidate))
    found.sort(key=lambda item: item[0])
    return [path for _, path in found]


def backup_file(src: str | Path, keep: int = DEFAULT_KEEP) -> Path:
    """Copy *src* to ``<src>.bak.<timestamp>`` and prune all but the newest *keep* backups.

    Returns the path of the backup just written. Raises ``FileNotFoundError`` when
    *src* does not exist and ``ValueError`` when *keep* is less than 1.
    """
    if keep < 1:
        raise ValueError("keep must be at least 1")
    src_path = Path(src)
    if not src_path.is_file():
        raise FileNotFoundError(f"Source file not found: {src_path}")

    stamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    backup_path = src_path.parent / f"{src_path.name}.bak.{stamp}"
    counter = 0
    while backup_path.exists():
        counter += 1
        backup_path = src_path.parent / f"{src_path.name}.bak.{stamp}.{counter}"
    shutil.copy2(src_path, backup_path)

    backups = list_backups(src_path)
    for old in backups[: max(0, len(backups) - keep)]:
        old.unlink()
    return backup_path


def restore_latest(src: str | Path) -> Path:
    """Put the newest backup of *src* back in place and consume it.

    Calling it repeatedly walks back through older backups. Returns the backup
    that was restored. Raises ``FileNotFoundError`` when there is none.
    """
    src_path = Path(src)
    backups = list_backups(src_path)
    if not backups:
        raise FileNotFoundError(f"no backups found for {src_path}")
    newest = backups[-1]
    shutil.copyfile(newest, src_path)
    newest.unlink()
    return newest
