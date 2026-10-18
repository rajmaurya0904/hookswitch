"""Ordering, collisions and restore for hookswitch.backup."""

import pytest

from hookswitch import backup as backup_mod
from hookswitch.backup import backup_file, list_backups, restore_latest


def test_keep_below_one_is_rejected(tmp_path):
    src = tmp_path / "c.json"
    src.write_text("x")
    with pytest.raises(ValueError):
        backup_file(src, keep=0)


def test_missing_source_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        backup_file(tmp_path / "gone.json")


def test_directory_is_not_a_valid_source(tmp_path):
    with pytest.raises(FileNotFoundError):
        backup_file(tmp_path)


def test_rotation_follows_name_order_not_mtime(tmp_path):
    src = tmp_path / "c.json"
    for i in range(6):
        src.write_text(f"v{i}")
        backup_file(src, keep=2)
    assert [p.read_text() for p in list_backups(src)] == ["v4", "v5"]


def test_same_timestamp_does_not_overwrite(tmp_path, monkeypatch):
    class FrozenDatetime:
        @staticmethod
        def now():
            import datetime

            return datetime.datetime(2026, 1, 2, 3, 4, 5, 6)

    monkeypatch.setattr(backup_mod, "datetime", FrozenDatetime)
    src = tmp_path / "c.json"
    for i in range(12):
        src.write_text(f"v{i}")
        backup_file(src, keep=20)
    contents = [p.read_text() for p in list_backups(src)]
    assert contents == [f"v{i}" for i in range(12)]


def test_unrelated_files_survive_pruning(tmp_path):
    src = tmp_path / "c.json"
    src.write_text("x")
    keepsake = tmp_path / "c.json.bak.old"
    keepsake.write_text("mine")
    other = tmp_path / "other.json.bak.20260101000000000000"
    other.write_text("not ours")
    for _ in range(5):
        backup_file(src, keep=1)
    assert keepsake.exists()
    assert other.exists()
    assert len(list_backups(src)) == 1


def test_list_backups_without_directory(tmp_path):
    assert list_backups(tmp_path / "missing" / "c.json") == []


def test_restore_latest_returns_content_and_consumes_backup(tmp_path):
    src = tmp_path / "c.json"
    src.write_text("one")
    backup_file(src)
    src.write_text("two")
    backup_file(src)
    src.write_text("three")
    used = restore_latest(src)
    assert src.read_text() == "two"
    assert not used.exists()
    restore_latest(src)
    assert src.read_text() == "one"
    with pytest.raises(FileNotFoundError):
        restore_latest(src)
