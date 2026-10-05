"""Tests for backup rotation."""

from hookswitch.backup import backup_file


def test_backup_rotation(tmp_path):
    src = tmp_path / "config.txt"
    src.write_text("initial")
    keep = 3
    # Create more backups than keep
    for _i in range(5):
        backup_file(src, keep=keep)
    # List backup files
    backup_files = list(tmp_path.glob("config.txt.bak.*"))
    # Should have exactly `keep` files
    assert len(backup_files) == keep
    # Ensure they are the most recent ones by modification time
    backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    # Each file should exist
    for f in backup_files:
        assert f.exists()