from .conftest import headers


def test_drawing_filters_and_pagination(client):
    project_id = client.get("/api/projects", headers=headers("admin")).json()[0]["id"]
    for no, title in (("SW-2026-921", "Alpha 板"), ("SW-2026-922", "Beta 板")):
        assert client.post(
            "/api/drawings",
            json={"project_id": project_id, "drawing_no": no, "title": title},
            headers=headers("designer"),
        ).status_code == 201

    by_q = client.get("/api/drawings", params={"q": "Alpha"}, headers=headers("designer")).json()
    assert [d["drawing_no"] for d in by_q] == ["SW-2026-921"]

    by_status = client.get("/api/drawings", params={"status": "draft"}, headers=headers("designer")).json()
    assert len(by_status) == 2

    page_resp = client.get("/api/drawings", params={"limit": 1}, headers=headers("designer"))
    assert len(page_resp.json()) == 1
    assert page_resp.headers["X-Total-Count"] == "2"
