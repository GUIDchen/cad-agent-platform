from .conftest import headers

EICAR = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"


def _drawing(client, no: str) -> int:
    project_id = client.get("/api/projects", headers=headers("admin")).json()[0]["id"]
    return client.post(
        "/api/drawings",
        json={"project_id": project_id, "drawing_no": no, "title": "病毒扫描"},
        headers=headers("designer"),
    ).json()["id"]


def test_upload_rejects_eicar(client):
    drawing_id = _drawing(client, "SW-2026-801")
    resp = client.post(
        f"/api/drawings/{drawing_id}/versions",
        files={"file": ("bad.dxf", EICAR, "application/dxf")},
        headers=headers("designer"),
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "VIRUS"
