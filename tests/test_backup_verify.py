import sqlite3
from pathlib import Path

from tools.backup import create_backup
from tools.backup_verify import verify_backup


def _make_backup(tmp_path: Path) -> Path:
    db = tmp_path / "app.db"
    conn = sqlite3.connect(db)
    conn.execute("create table users (id integer primary key, name text)")
    conn.execute("insert into users (name) values ('admin')")
    conn.commit()
    conn.close()
    storage = tmp_path / "storage"
    storage.mkdir()
    (storage / "a.dxf").write_text("dxf", encoding="utf-8")
    return create_backup(f"sqlite:///{db}", storage, tmp_path / "backups", keep=2)


def test_verify_backup_ok(tmp_path: Path):
    backup = _make_backup(tmp_path)
    report = verify_backup(backup)
    assert report["ok"] is True
    assert report["errors"] == []


def test_verify_backup_detects_corruption(tmp_path: Path):
    backup = _make_backup(tmp_path)
    db = backup / "app.db"
    db.write_bytes(db.read_bytes() + b"x")
    report = verify_backup(backup)
    assert report["ok"] is False
    assert any("sha256" in error or "大小" in error for error in report["errors"])
