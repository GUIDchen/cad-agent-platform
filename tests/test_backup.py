import json
from pathlib import Path

from tools.backup import create_backup


def test_backup_and_retention(tmp_path: Path):
    db = tmp_path / "app.db"
    db.write_bytes(b"sqlite-bytes")
    storage = tmp_path / "storage"
    storage.mkdir()
    (storage / "a.dxf").write_text("dxf", encoding="utf-8")

    out = tmp_path / "backups"
    first = create_backup(f"sqlite:///{db}", storage, out, keep=2)
    manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
    assert (first / "app.db").read_bytes() == b"sqlite-bytes"
    assert (first / "storage.tar.gz").exists()
    assert manifest["files"]

    second = create_backup(f"sqlite:///{db}", storage, out, keep=2)
    third = create_backup(f"sqlite:///{db}", storage, out, keep=2)
    remaining = sorted(p.name for p in out.iterdir())
    assert len(remaining) == 2
    assert first.name not in remaining
    assert second.name in remaining
    assert third.name in remaining


def test_dry_run(tmp_path: Path):
    out = tmp_path / "backups"
    target = create_backup(f"sqlite:///{tmp_path}/nope.db", tmp_path, out, dry_run=True)
    assert not target.exists()
