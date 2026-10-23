from .conftest import headers


def _generated_version(client, no: str) -> int:
    project_id = client.get("/api/projects", headers=headers("admin")).json()[0]["id"]
    drawing = client.post(
        "/api/drawings",
        json={"project_id": project_id, "drawing_no": no, "title": "卡片审批"},
        headers=headers("designer"),
    ).json()
    gen = client.post(
        f"/api/drawings/{drawing['id']}/generate",
        json={"length": 180, "width": 120, "holes": [{"x": 20, "y": 20, "d": 6.6}]},
        headers=headers("designer"),
    ).json()
    assert client.get(f"/api/jobs/{gen['job_id']}", headers=headers("designer")).json()["status"] == "done"
    return client.get(f"/api/drawings/{drawing['id']}/versions", headers=headers("designer")).json()[0]["id"]


def test_wecom_action_approve(client):
    version_id = _generated_version(client, "SW-2026-501")
    resp = client.post(
        "/api/wecom/action",
        json={"action": "approve", "version_id": version_id},
        headers={"X-Wecom-Token": "dev-wecom-action"},
    )
    assert resp.status_code == 200
    version = client.get(f"/api/versions/{version_id}/preview", headers=headers("reviewer"))
    assert version.status_code == 200


def test_wecom_action_reject_requires_comment(client):
    version_id = _generated_version(client, "SW-2026-502")
    resp = client.post(
        "/api/wecom/action",
        json={"action": "reject", "version_id": version_id},
        headers={"X-Wecom-Token": "dev-wecom-action"},
    )
    assert resp.status_code == 200


def test_wecom_action_bad_token(client):
    version_id = _generated_version(client, "SW-2026-503")
    resp = client.post(
        "/api/wecom/action",
        json={"action": "approve", "version_id": version_id},
        headers={"X-Wecom-Token": "wrong"},
    )
    assert resp.status_code == 401
