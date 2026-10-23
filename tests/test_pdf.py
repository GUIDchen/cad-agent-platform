from .conftest import headers


def test_version_pdf(client):
    project_id = client.get("/api/projects", headers=headers("admin")).json()[0]["id"]
    drawing = client.post(
        "/api/drawings",
        json={"project_id": project_id, "drawing_no": "SW-2026-951", "title": "PDF"},
        headers=headers("designer"),
    ).json()
    client.post(
        f"/api/drawings/{drawing['id']}/generate",
        json={"length": 180, "width": 120, "holes": [{"x": 20, "y": 20, "d": 6.6}]},
        headers=headers("designer"),
    )
    version = client.get(f"/api/drawings/{drawing['id']}/versions", headers=headers("designer")).json()[0]
    resp = client.get(f"/api/versions/{version['id']}/pdf", headers=headers("designer"))
    assert resp.status_code == 200
    assert resp.content.startswith(b"%PDF")
