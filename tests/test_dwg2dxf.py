from pathlib import Path

import pytest

from app.core.dwg import convert


def _fake_converter(tmp_path: Path) -> Path:
    script = tmp_path / "fake-dwg2dxf.sh"
    script.write_text("#!/bin/sh\ncp \"$1\" \"$2\"\n", encoding="utf-8")
    script.chmod(0o755)
    return script


def test_convert_with_fake_binary(tmp_path: Path, monkeypatch):
    src = tmp_path / "a.dwg"
    src.write_bytes(b"DXF-CONTENT")
    dst = tmp_path / "a.dxf"
    monkeypatch.setenv("DWG2DXF_BIN", str(_fake_converter(tmp_path)))
    assert convert(src, dst) == dst
    assert dst.read_bytes() == b"DXF-CONTENT"


def test_convert_without_converter(tmp_path: Path, monkeypatch):
    src = tmp_path / "a.dwg"
    src.write_bytes(b"x")
    monkeypatch.delenv("DWG2DXF_BIN", raising=False)
    monkeypatch.delenv("ODA_FILE_CONVERTER", raising=False)
    with pytest.raises(RuntimeError):
        convert(src, tmp_path / "a.dxf")
