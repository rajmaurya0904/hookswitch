"""Tests for hookswitch.backup."""

from hookswitch.backup import backup_file


def test_backup_creates_timestamped_bak_with_identical_content(tmp_path):
    src = tmp_path / "config.json"
    src.write_text('{"servers": {"a": {"enabled": true}}}')
    backup = backup_file(src)
    # Backup should be named <src>.bak.<timestamp>
    assert backup.name.startswith(src.name + ".bak.")
    assert backup.parent == src.parent
    assert backup.exists()
    assert backup.read_text() == src.read_text()


def test_backup_does_not_modify_original(tmp_path):
    src = tmp_path / "config.json"
    src.write_text("original")
    backup_file(src)
    assert src.read_text() == "original"


def test_backup_keeps_most_recent_N(tmp_path):
    src = tmp_path / "config.json"
    src.write_text("v1")
    # First backup
    backup_file(src, keep=3)
    src.write_text("v2")
    backup_file(src, keep=3)
    src.write_text("v3")
    backup_file(src, keep=3)
    src.write_text("v4")
    backup_file(src, keep=3)

    # List backup files
    pattern = f"{src.name}.bak.*"
    backups = list(src.parent.glob(pattern))
    # Should have at most 3 backups
    assert len(backups) <= 3
    # Actually, we expect exactly 3 because we called backup_file 4 times with keep=3
    assert len(backups) == 3
    # The content of the most recent backup should be the latest source ("v4")
    # Determine most recent by modification time
    latest = max(backups, key=lambda p: p.stat().st_mtime)
    assert latest.read_text() == "v4"


def test_backup_default_keep_is_3(tmp_path):
    src = tmp_path / "config.json"
    src.write_text("v1")
    for i in range(2, 6):  # v2, v3, v4, v5
        src.write_text(f"v{i}")
        backup_file(src)  # default keep=3

    pattern = f"{src.name}.bak.*"
    backups = list(src.parent.glob(pattern))
    assert len(backups) == 3
    # The three most recent should be v3, v4, v5? Let's check.
    # Actually, after 5 backups (v1..v5) with keep=3, we should have v3, v4, v5.
    contents = sorted(b.read_text() for b in backups)
    assert contents == ["v3", "v4", "v5"]