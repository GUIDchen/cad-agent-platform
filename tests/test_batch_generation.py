from app.api import generation as generation_module

from .conftest import headers


def test_batch_generate(client, monkeypatch):
    monkeypatch.setattr(generation_module, "EXECUTION_MODE", "external")
    project_id = client.get("/api/projects", headers=headers("admin")).json()[0]["id"]
    ids = []
    for index in (1, 2):
        resp = client.post(
            "/api/drawings",
            json={"project_id": project_id, "drawing_no": f"SW-2026-88{index}", "title": f"批量{index}"},
            headers=headers("designer"),
        )
        ids.append(resp.json()["id"])

    payload = {
        "items": [
            {"drawing_id": ids[0], "spec": {"length": 180, "width": 120, "holes": [{"x": 20, "y": 20, "d": 6.6}]}},
            {"drawing_id": ids[1], "spec": {"length": 200, "width": 100, "holes": [{"x": 20, "y": 20, "d": 6.6}]}},
        ]
    }
    resp = client.post("/api/drawings/batch-generate", json=payload, headers=headers("designer"))
    assert resp.status_code == 200
    assert len(resp.json()) == 2
    assert all(item["status"] == "queued" for item in resp.json())
