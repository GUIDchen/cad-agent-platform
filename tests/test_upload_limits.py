
from .conftest import headers

from app.services import upload as upload_service


def _drawing(client, no: str) -> int:
    project_id = client.get("/api/projects", headers=headers("admin")).json()[0]["id"]
    return client.post(
        "/api/drawings",
        json={"project_id": project_id, "drawing_no": no, "title": "上传限制"},
        headers=headers("designer"),
    ).json()["id"]


def test_upload_rejects_invalid_dxf(client):
    drawing_id = _drawing(client, "SW-2026-811")
    resp = client.post(
        f"/api/drawings/{drawing_id}/versions",
        files={"file": ("bad.dxf", b"not a dxf", "application/dxf")},
        headers=headers("designer"),
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "BAD_DXF"


def test_upload_rejects_too_large(client, monkeypatch):
    drawing_id = _drawing(client, "SW-2026-812")
    monkeypatch.setattr(upload_service, "MAX_UPLOAD_BYTES", 10)
    resp = client.post(
        f"/api/drawings/{drawing_id}/versions",
        files={"file": ("big.dxf", b"0\nSECTION\n" + b"x" * 100, "application/dxf")},
        headers=headers("designer"),
    )
    assert resp.status_code == 413
