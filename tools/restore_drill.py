import argparse
import json
import sqlite3
import tempfile
from pathlib import Path

from tools.restore import restore_backup

REQUIRED_TABLES = [
    "users",
    "projects",
    "project_members",
    "drawings",
    "versions",
    "jobs",
    "approvals",
    "audit_logs",
    "notifications",
    "comments",
    "knowledge_docs",
]


def run_drill(backup_dir: Path, target_dir: Path | None = None) -> dict:
    target = Path(target_dir) if target_dir else Path(tempfile.mkdtemp(prefix="restore-drill-"))
    manifest = restore_backup(Path(backup_dir), target)
    db_path = target / "app.db"
    tables: list[str] = []
    counts: dict[str, int] = {}
    missing: list[str] = []

    if db_path.exists():
        conn = sqlite3.connect(db_path)
        tables = sorted(row[0] for row in conn.execute("select name from sqlite_master where type='table'"))
        missing = [name for name in REQUIRED_TABLES if name not in tables]
        for name in REQUIRED_TABLES:
            if name in tables:
                counts[name] = conn.execute(f"select count(*) from {name}").fetchone()[0]
        conn.close()
    else:
        missing = list(REQUIRED_TABLES)

    storage_files = 0
    storage = target / "storage"
    if storage.exists():
        storage_files = sum(1 for item in storage.rglob("*") if item.is_file())

    return {
        "ok": not missing,
        "backup": str(backup_dir),
        "target": str(target),
        "tables": tables,
        "missing": missing,
        "counts": counts,
        "storage_files": storage_files,
        "manifest_files": len(manifest.get("files", [])),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--backup", required=True)
    parser.add_argument("--target", default=None)
    parser.add_argument("--report", default=None)
    args = parser.parse_args()
    report = run_drill(Path(args.backup), Path(args.target) if args.target else None)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    if args.report:
        Path(args.report).write_text(text, encoding="utf-8")
    raise SystemExit(0 if report["ok"] else 1)
