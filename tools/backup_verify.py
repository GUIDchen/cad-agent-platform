import argparse
import json
import sqlite3
import tarfile
from pathlib import Path

from tools.backup import _sha256


def verify_backup(path: Path) -> dict:
    path = Path(path)
    errors: list[str] = []
    manifest_path = path / "manifest.json"
    if not manifest_path.exists():
        return {"ok": False, "errors": ["缺少 manifest.json"], "files": 0}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest.get("files", []):
        target = path / entry["name"]
        if not target.exists():
            errors.append(f"缺少文件 {entry['name']}")
            continue
        if target.stat().st_size != entry.get("size"):
            errors.append(f"大小不一致 {entry['name']}")
        if _sha256(target) != entry.get("sha256"):
            errors.append(f"sha256 不一致 {entry['name']}")

    db = path / "app.db"
    if db.exists():
        try:
            conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            result = conn.execute("pragma integrity_check").fetchone()[0]
            conn.close()
            if result != "ok":
                errors.append(f"SQLite 完整性失败: {result}")
        except sqlite3.DatabaseError as exc:
            errors.append(f"SQLite 无法打开: {exc}")

    archive = path / "storage.tar.gz"
    if archive.exists():
        try:
            with tarfile.open(archive, "r:gz") as tar:
                tar.getnames()
        except Exception as exc:  # noqa: BLE001
            errors.append(f"存储归档损坏: {exc}")

    return {"ok": not errors, "errors": errors, "files": len(manifest.get("files", []))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    report = verify_backup(Path(args.path))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["ok"] else 1)
