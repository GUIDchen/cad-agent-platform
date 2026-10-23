import argparse
import hashlib
import json
import shutil
import tarfile
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest(backup_dir: Path) -> dict:
    manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
    for item in manifest.get("files", []):
        path = backup_dir / item["name"]
        if not path.exists():
            raise FileNotFoundError(path)
        if _sha256(path) != item["sha256"]:
            raise ValueError(f"校验失败: {item['name']}")
    return manifest


def restore_backup(backup_dir: Path, target_dir: Path, dry_run: bool = False) -> dict:
    manifest = verify_manifest(backup_dir)
    if dry_run:
        return manifest

    target_dir.mkdir(parents=True, exist_ok=True)
    for item in manifest.get("files", []):
        src = backup_dir / item["name"]
        if item["name"] == "storage.tar.gz":
            with tarfile.open(src, "r:gz") as tar:
                tar.extractall(target_dir, filter="data")
        else:
            shutil.copy2(src, target_dir / item["name"])
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--backup", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    data = restore_backup(Path(args.backup), Path(args.target), dry_run=args.dry_run)
    print(f"restored={args.backup} target={args.target} files={len(data.get('files', []))}")
