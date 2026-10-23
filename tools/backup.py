import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sqlite_path(database_url: str) -> Path:
    return Path(database_url.replace("sqlite:///", "", 1))


def apply_retention(out_dir: Path, keep: int) -> list[Path]:
    backups = sorted([p for p in out_dir.iterdir() if p.is_dir() and p.name.startswith("backup-")])
    removed = []
    for old in backups[:-keep] if keep > 0 else backups:
        shutil.rmtree(old)
        removed.append(old)
    return removed


def create_backup(database_url: str, storage_dir: Path, out_dir: Path, keep: int = 7, dry_run: bool = False) -> Path:
    stamp = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y%m%d-%H%M%S-%f")
    dest = out_dir / f"backup-{stamp}"
    if dry_run:
        print(f"[dry-run] would create {dest}")
        return dest

    dest.mkdir(parents=True, exist_ok=False)
    files: list[dict] = []

    if database_url.startswith("sqlite:///"):
        src = _sqlite_path(database_url)
        if not src.exists():
            raise FileNotFoundError(src)
        target = dest / "app.db"
        shutil.copy2(src, target)
        files.append({"name": "app.db", "sha256": _sha256(target), "size": target.stat().st_size})
    else:
        target = dest / "db.sql"
        with target.open("wb") as fh:
            subprocess.run(["pg_dump", database_url], stdout=fh, check=True)
        files.append({"name": "db.sql", "sha256": _sha256(target), "size": target.stat().st_size})

    if storage_dir.exists():
        archive = dest / "storage.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(storage_dir, arcname="storage")
        files.append({"name": "storage.tar.gz", "sha256": _sha256(archive), "size": archive.stat().st_size})

    manifest = {
        "created_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        "database": "sqlite" if database_url.startswith("sqlite:///") else "postgres",
        "files": files,
    }
    (dest / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    apply_retention(out_dir, keep)
    return dest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL", "sqlite:///backend/data/app.db"))
    parser.add_argument("--storage-dir", default=os.getenv("STORAGE_DIR", "backend/data/storage"))
    parser.add_argument("--out", default="backups")
    parser.add_argument("--keep", type=int, default=7)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = create_backup(
        args.database_url,
        Path(args.storage_dir),
        Path(args.out),
        keep=args.keep,
        dry_run=args.dry_run,
    )
    print(f"backup={result}")
