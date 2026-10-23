from pathlib import Path

from app.core.bracket import build

from .conftest import headers

SPEC = {
    "drawing_no": "SW-2026-701",
    "title": "上传测试",
    "length": 180,
    "width": 120,
    "material": "304",
    "surface": "拉丝",
    "holes": [{"x": 20, "y": 20, "d": 6.6}, {"x": 160, "y": 100, "d": 6.6}],
}


def _drawing(client, no: str) -> int:
    project_id = client.get("/api/projects", headers=headers("admin")).json()[0]["id"]
    return client.post(
        "/api/drawings",
        json={"project_id": project_id, "drawing_no": no, "title": "上传测试"},
        headers=headers("designer"),
    ).json()["id"]


def test_upload_dxf_version(client, tmp_path: Path):
    drawing_id = _drawing(client, "SW-2026-701")
    spec = dict(SPEC)
    spec["drawing_no"] = "SW-2026-701"
    dxf = build(spec, tmp_path / "upload.dxf")
    content = dxf.read_bytes()

    resp = client.post(
        f"/api/drawings/{drawing_id}/versions",
        files={"file": ("upload.dxf", content, "application/dxf")},
        headers=headers("designer"),
    )
    assert resp.status_code == 201, resp.text
    version = resp.json()
    assert version["version"] == 1

    preview = client.get(f"/api/versions/{version['id']}/preview", headers=headers("designer"))
    assert preview.status_code == 200
    assert preview.headers["content-type"].startswith("image/png")


def _fake_converter(tmp_path: Path) -> Path:
    script = tmp_path / "fake-dwg2dxf.sh"
    script.write_text("#!/bin/sh\ncp \"$1\" \"$2\"\n", encoding="utf-8")
    script.chmod(0o755)
    return script


def test_upload_dwg_with_converter(client, tmp_path: Path, monkeypatch):
    drawing_id = _drawing(client, "SW-2026-703")
    spec = dict(SPEC)
    spec["drawing_no"] = "SW-2026-703"
    content = build(spec, tmp_path / "source.dxf").read_bytes()
    monkeypatch.setenv("DWG2DXF_BIN", str(_fake_converter(tmp_path)))

    resp = client.post(
        f"/api/drawings/{drawing_id}/versions",
        files={"file": ("part.dwg", content, "application/acad")},
        headers=headers("designer"),
    )
    assert resp.status_code == 201, resp.text


def test_upload_dwg_without_converter(client, tmp_path: Path, monkeypatch):
    drawing_id = _drawing(client, "SW-2026-704")
    content = build(SPEC, tmp_path / "source2.dxf").read_bytes()
    monkeypatch.delenv("DWG2DXF_BIN", raising=False)
    monkeypatch.delenv("ODA_FILE_CONVERTER", raising=False)
    resp = client.post(
        f"/api/drawings/{drawing_id}/versions",
        files={"file": ("part.dwg", content, "application/acad")},
        headers=headers("designer"),
    )
    assert resp.status_code == 400


def test_upload_rejects_non_dxf(client):
    drawing_id = _drawing(client, "SW-2026-702")
    resp = client.post(
        f"/api/drawings/{drawing_id}/versions",
        files={"file": ("notes.txt", b"hello", "text/plain")},
        headers=headers("designer"),
    )
    assert resp.status_code == 400
