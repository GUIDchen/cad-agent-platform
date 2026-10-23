import json
import os
from pathlib import Path

from .conftest import headers


def test_push_bom_to_mock_outbox(client):
    project_id = client.get("/api/projects", headers=headers("admin")).json()[0]["id"]
    drawing = client.post(
        "/api/drawings",
        json={"project_id": project_id, "drawing_no": "SW-2026-901", "title": "ERP 测试"},
        headers=headers("designer"),
    ).json()
    gen = client.post(
        f"/api/drawings/{drawing['id']}/generate",
        json={"length": 180, "width": 120, "holes": [{"x": 20, "y": 20, "d": 6.6}]},
        headers=headers("designer"),
    ).json()
    assert client.get(f"/api/jobs/{gen['job_id']}", headers=headers("designer")).json()["status"] == "done"

    resp = client.post(f"/api/drawings/{drawing['id']}/bom/push", headers=headers("designer"))
    assert resp.status_code == 200, resp.text
    assert resp.json()["mode"] == "mock"

    outbox = Path(os.environ["DATA_DIR"]) / "erp_outbox.jsonl"
    record = json.loads(outbox.read_text(encoding="utf-8").splitlines()[-1])
    assert record["drawing_no"] == "SW-2026-901"
    assert "图号" in record["bom_csv"]
