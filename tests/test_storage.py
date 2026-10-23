from pathlib import Path

from app.storage import LocalStorage, sha256_file, version_keys


def test_version_keys():
    assert version_keys("SW-2026-001", 2) == ("SW-2026-001/v2.dxf", "SW-2026-001/v2.png")


def test_local_storage_roundtrip(tmp_path: Path):
    store = LocalStorage(tmp_path / "root")
    src = tmp_path / "a.txt"
    src.write_text("hello", encoding="utf-8")
    store.save(src, "SW-2026-001/v1.dxf")
    assert store.exists("SW-2026-001/v1.dxf")
    assert store.local_path("SW-2026-001/v1.dxf").read_text(encoding="utf-8") == "hello"
    assert not store.exists("missing.dxf")


def test_absolute_path_compat(tmp_path: Path):
    store = LocalStorage(tmp_path / "root")
    abs_path = tmp_path / "abs.dxf"
    abs_path.write_text("x", encoding="utf-8")
    assert store.local_path(str(abs_path)) == abs_path


def test_sha256(tmp_path: Path):
    p = tmp_path / "a.txt"
    p.write_text("hello", encoding="utf-8")
    assert sha256_file(p) == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
