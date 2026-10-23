import sys
from pathlib import Path

from tools.adapter_smoke import run_adapter


def _fake_adapter(path: Path, with_dxf: bool = True) -> Path:
    script = path / "adapter.py"
    body = "import pathlib, sys\nsys.stdin.read()\n"
    if with_dxf:
        body += "pathlib.Path('out.dxf').write_text('0\\nSECTION\\n2\\nENTITIES\\n0\\nENDSEC\\n0\\nEOF')\n"
    script.write_text(body, encoding="utf-8")
    return script


def test_adapter_smoke_ok(tmp_path: Path):
    script = _fake_adapter(tmp_path)
    report = run_adapter(f"{sys.executable} {script}")
    assert report["ok"] is True
    assert report["dxf_has_section"] is True


def test_adapter_smoke_missing_output(tmp_path: Path):
    script = _fake_adapter(tmp_path, with_dxf=False)
    report = run_adapter(f"{sys.executable} {script}")
    assert report["ok"] is False


def test_example_adapter():
    root = Path(__file__).resolve().parents[1]
    report = run_adapter(f"{sys.executable} {root / 'worker' / 'adapters' / 'example_adapter.py'}")
    assert report["ok"] is True
