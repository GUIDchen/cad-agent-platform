from .conftest import headers


def test_comments_roundtrip(client):
    project_id = client.get("/api/projects", headers=headers("admin")).json()[0]["id"]
    drawing = client.post(
        "/api/drawings",
        json={"project_id": project_id, "drawing_no": "SW-2026-971", "title": "讨论"},
        headers=headers("designer"),
    ).json()

    created = client.post(
        f"/api/drawings/{drawing['id']}/comments",
        json={"body": "这个孔位需要确认"},
        headers=headers("designer"),
    )
    assert created.status_code == 201
    assert created.json()["author_name"] == "designer"

    rows = client.get(f"/api/drawings/{drawing['id']}/comments", headers=headers("reviewer")).json()
    assert len(rows) == 1
    assert rows[0]["body"] == "这个孔位需要确认"
