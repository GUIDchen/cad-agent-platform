import sqlite3
from pathlib import Path

from tools.backup import create_backup
from tools.restore_drill import REQUIRED_TABLES, run_drill


def _db(path: Path):
    conn = sqlite3.connect(path)
    for table in REQUIRED_TABLES:
        conn.execute(f"create table {table} (id integer primary key, value text)")
    conn.execute("insert into users (value) values ('admin')")
    conn.commit()
    conn.close()


def test_restore_drill_ok(tmp_path: Path):
    db = tmp_path / "app.db"
    _db(db)
    storage = tmp_path / "storage"
    storage.mkdir()
    (storage / "a.dxf").write_text("dxf", encoding="utf-8")
    backup = create_backup(f"sqlite:///{db}", storage, tmp_path / "backups", keep=2)

    report = run_drill(backup, tmp_path / "restored")
    assert report["ok"] is True
    assert report["missing"] == []
    assert report["counts"]["users"] == 1
    assert report["storage_files"] == 1


def test_restore_drill_detects_missing_table(tmp_path: Path):
    db = tmp_path / "app.db"
    conn = sqlite3.connect(db)
    conn.execute("create table users (id integer primary key)")
    conn.commit()
    conn.close()
    backup = create_backup(f"sqlite:///{db}", tmp_path, tmp_path / "backups", keep=2)
    report = run_drill(backup, tmp_path / "restored")
    assert report["ok"] is False
    assert "drawings" in report["missing"]
