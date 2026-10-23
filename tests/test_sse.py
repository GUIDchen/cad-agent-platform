from .conftest import headers


def test_job_events_stream(client):
    project_id = client.get("/api/projects", headers=headers("admin")).json()[0]["id"]
    drawing = client.post(
        "/api/drawings",
        json={"project_id": project_id, "drawing_no": "SW-2026-931", "title": "SSE"},
        headers=headers("designer"),
    ).json()
    job = client.post(
        f"/api/drawings/{drawing['id']}/generate",
        json={"length": 180, "width": 120, "holes": [{"x": 20, "y": 20, "d": 6.6}]},
        headers=headers("designer"),
    ).json()

    resp = client.get(f"/api/jobs/{job['job_id']}/events", headers=headers("designer"))
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    assert "data:" in resp.text
    assert "done" in resp.text
