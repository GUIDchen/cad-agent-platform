from .conftest import headers


def _new_drawing(client, no: str) -> int:
    project_id = client.get("/api/projects", headers=headers("admin")).json()[0]["id"]
    drawing = client.post(
        "/api/drawings",
        json={"project_id": project_id, "drawing_no": no, "title": "锁测试"},
        headers=headers("designer"),
    ).json()
    return drawing["id"]


def test_lock_conflict(client):
    drawing_id = _new_drawing(client, "SW-2026-101")
    first = client.post(f"/api/drawings/{drawing_id}/checkout", headers=headers("designer"))
    assert first.status_code == 200
    second = client.post(f"/api/drawings/{drawing_id}/checkout", headers=headers("designer2"))
    assert second.status_code == 409
    client.post(f"/api/drawings/{drawing_id}/checkin", headers=headers("designer"))


def test_viewer_cannot_generate(client):
    drawing_id = _new_drawing(client, "SW-2026-102")
    resp = client.post(
        f"/api/drawings/{drawing_id}/generate",
        json={"length": 100, "width": 100, "holes": [{"x": 10, "y": 10, "d": 6}]},
        headers=headers("viewer"),
    )
    assert resp.status_code == 403


def test_reject_requires_comment(client):
    drawing_id = _new_drawing(client, "SW-2026-103")
    gen = client.post(
        f"/api/drawings/{drawing_id}/generate",
        json={"length": 100, "width": 100, "holes": [{"x": 10, "y": 10, "d": 6}]},
        headers=headers("designer"),
    ).json()
    assert client.get(f"/api/jobs/{gen['job_id']}", headers=headers("designer")).json()["status"] == "done"
    version_id = client.get(f"/api/drawings/{drawing_id}/versions", headers=headers("designer")).json()[0]["id"]
    resp = client.post(f"/api/versions/{version_id}/reject", json={"comment": ""}, headers=headers("reviewer"))
    assert resp.status_code == 422
