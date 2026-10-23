from pathlib import Path

import pytest

from tools.backup import create_backup
from tools.restore import restore_backup, verify_manifest


def test_restore_roundtrip(tmp_path: Path):
    db = tmp_path / "app.db"
    db.write_bytes(b"sqlite-bytes")
    storage = tmp_path / "storage"
    storage.mkdir()
    (storage / "a.dxf").write_text("dxf", encoding="utf-8")

    backup = create_backup(f"sqlite:///{db}", storage, tmp_path / "backups", keep=3)
    target = tmp_path / "restored"
    manifest = restore_backup(backup, target)
    assert manifest["files"]
    assert (target / "app.db").read_bytes() == b"sqlite-bytes"
    assert (target / "storage" / "a.dxf").read_text(encoding="utf-8") == "dxf"


def test_manifest_detects_tamper(tmp_path: Path):
    db = tmp_path / "app.db"
    db.write_bytes(b"sqlite-bytes")
    backup = create_backup(f"sqlite:///{db}", tmp_path, tmp_path / "backups", keep=3)
    (backup / "app.db").write_bytes(b"tampered")
    with pytest.raises(ValueError):
        verify_manifest(backup)


def test_dry_run_does_not_write(tmp_path: Path):
    db = tmp_path / "app.db"
    db.write_bytes(b"sqlite-bytes")
    backup = create_backup(f"sqlite:///{db}", tmp_path, tmp_path / "backups", keep=3)
    target = tmp_path / "restored"
    restore_backup(backup, target, dry_run=True)
    assert not target.exists()
