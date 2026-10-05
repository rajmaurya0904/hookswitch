"""Tests for hookswitch.backup."""

from hookswitch.backup import backup_file


def test_backup_creates_bak_with_identical_content(tmp_path):
    src = tmp_path / "config.json"
    src.write_text('{"servers": {"a": {"enabled": true}}}')
    backup = backup_file(src)
    assert backup == tmp_path / "config.json.bak"
    assert backup.exists()
    assert backup.read_text() == src.read_text()


def test_backup_does_not_modify_original(tmp_path):
    src = tmp_path / "config.json"
    src.write_text("original")
    backup_file(src)
    assert src.read_text() == "original"


def test_backup_overwrites_existing_backup(tmp_path):
    src = tmp_path / "config.json"
    src.write_text("v1")
    backup_file(src)
    src.write_text("v2")
    backup = backup_file(src)
    assert backup.read_text() == "v2"
