from .conftest import headers


def test_pending_approvals(client):
    project_id = client.get("/api/projects", headers=headers("admin")).json()[0]["id"]
    drawing = client.post(
        "/api/drawings",
        json={"project_id": project_id, "drawing_no": "SW-2026-941", "title": "待办"},
        headers=headers("designer"),
    ).json()
    client.post(
        f"/api/drawings/{drawing['id']}/generate",
        json={"length": 180, "width": 120, "holes": [{"x": 20, "y": 20, "d": 6.6}]},
        headers=headers("designer"),
    )

    rows = client.get("/api/approvals/pending", headers=headers("reviewer")).json()
    assert any(row["drawing_no"] == "SW-2026-941" for row in rows)
    assert client.get("/api/approvals/pending", headers=headers("designer")).status_code == 403
