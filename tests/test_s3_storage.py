from pathlib import Path

from moto import mock_aws

from app import storage


def test_s3_storage_roundtrip(tmp_path: Path, monkeypatch):
    with mock_aws():
        monkeypatch.setattr(storage, "S3_BUCKET", "cad-test")
        monkeypatch.setattr(storage, "S3_ENDPOINT", "")
        store = storage.S3Storage()
        src = tmp_path / "a.txt"
        src.write_text("hello-s3", encoding="utf-8")

        store.save(src, "SW-2026-001/v1.dxf")
        assert store.exists("SW-2026-001/v1.dxf")
        cached = store.local_path("SW-2026-001/v1.dxf")
        assert cached.read_text(encoding="utf-8") == "hello-s3"
        assert store.health()
