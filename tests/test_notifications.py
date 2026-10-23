from .conftest import headers


def test_notifications_created_and_read(client):
    project_id = client.get("/api/projects", headers=headers("admin")).json()[0]["id"]
    drawing = client.post(
        "/api/drawings",
        json={"project_id": project_id, "drawing_no": "SW-2026-961", "title": "通知"},
        headers=headers("designer"),
    ).json()
    client.post(
        f"/api/drawings/{drawing['id']}/generate",
        json={"length": 180, "width": 120, "holes": [{"x": 20, "y": 20, "d": 6.6}]},
        headers=headers("designer"),
    )

    rows = client.get("/api/notifications", headers=headers("designer")).json()
    assert any("生成完成" in row["title"] for row in rows)
    assert client.get("/api/notifications/unread-count", headers=headers("designer")).json()["count"] >= 1

    target = next(row for row in rows if "生成完成" in row["title"])
    marked = client.post(f"/api/notifications/{target['id']}/read", headers=headers("designer"))
    assert marked.status_code == 200
    assert marked.json()["read"] is True
