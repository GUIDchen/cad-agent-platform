import os
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _alembic(db: Path, *args: str) -> None:
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{db}"}
    exe = Path(sys.executable).parent / "alembic"
    subprocess.run([str(exe), *args], cwd=ROOT, env=env, check=True, capture_output=True, text=True)


def test_alembic_upgrade_creates_schema(tmp_path):
    db = tmp_path / "migration.db"
    _alembic(db, "upgrade", "head")
    conn = sqlite3.connect(db)
    indexes = {row[0] for row in conn.execute("select name from sqlite_master where type='index'")}
    assert "ix_audit_logs_actor_id" in indexes
    assert "ix_drawings_status" in indexes

    tables = {row[0] for row in conn.execute("select name from sqlite_master where type='table'")}
    assert {
        "users",
        "projects",
        "project_members",
        "drawings",
        "versions",
        "jobs",
        "approvals",
        "audit_logs",
        "alembic_version",
    } <= tables


def test_alembic_downgrade_and_upgrade(tmp_path):
    db = tmp_path / "roundtrip.db"
    _alembic(db, "upgrade", "head")
    _alembic(db, "downgrade", "base")

    conn = sqlite3.connect(db)
    tables = {row[0] for row in conn.execute("select name from sqlite_master where type='table'")}
    assert "users" not in tables

    _alembic(db, "upgrade", "head")
    conn = sqlite3.connect(db)
    tables = {row[0] for row in conn.execute("select name from sqlite_master where type='table'")}
    assert "users" in tables
