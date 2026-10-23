import hashlib
import shutil
from functools import lru_cache
from pathlib import Path

from .config import (
    CACHE_DIR,
    S3_ACCESS_KEY,
    S3_BUCKET,
    S3_ENDPOINT,
    S3_REGION,
    S3_SECRET_KEY,
    STORAGE_BACKEND,
    STORAGE_DIR,
)


def version_keys(drawing_no: str, version: int) -> tuple[str, str]:
    """Return object keys for the DXF and PNG of a version."""
    return f"{drawing_no}/v{version}.dxf", f"{drawing_no}/v{version}.png"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class LocalStorage:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, src: Path, key: str) -> None:
        dest = self.root / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)

    def local_path(self, key: str) -> Path:
        path = Path(key)
        if path.is_absolute():
            return path
        return self.root / key

    def exists(self, key: str) -> bool:
        return (self.root / key).exists()

    def health(self) -> bool:
        try:
            probe = self.root / ".health"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            return True
        except Exception:  # noqa: BLE001
            return False


class S3Storage:
    def __init__(self):
        try:
            import boto3
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("STORAGE_BACKEND=s3 需要安装 boto3") from exc
        self.bucket = S3_BUCKET
        self.client = boto3.client(
            "s3",
            endpoint_url=S3_ENDPOINT or None,
            aws_access_key_id=S3_ACCESS_KEY or None,
            aws_secret_access_key=S3_SECRET_KEY or None,
            region_name=S3_REGION,
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except Exception:  # noqa: BLE001 - create if missing
            self.client.create_bucket(Bucket=self.bucket)

    def save(self, src: Path, key: str) -> None:
        self.client.upload_file(str(src), self.bucket, key)

    def local_path(self, key: str) -> Path:
        if Path(key).is_absolute():
            return Path(key)
        dest = CACHE_DIR / key
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            self.client.download_file(self.bucket, key, str(dest))
        return dest

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:  # noqa: BLE001
            return False

    def health(self) -> bool:
        try:
            self.client.head_bucket(Bucket=self.bucket)
            return True
        except Exception:  # noqa: BLE001
            return False


@lru_cache(maxsize=1)
def get_storage():
    if STORAGE_BACKEND == "s3":
        return S3Storage()
    return LocalStorage(STORAGE_DIR)
