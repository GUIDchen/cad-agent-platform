from .conftest import headers


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_request_id_and_metrics(client):
    resp = client.get("/api/health")
    assert resp.headers.get("X-Request-Id")

    metrics = client.get("/api/metrics")
    assert metrics.status_code == 200
    assert "cad_requests_total" in metrics.text
    assert "cad_drawings_total" in metrics.text


def test_version(client):
    resp = client.get("/api/version")
    assert resp.status_code == 200
    assert resp.json()["version"]


def test_ready(client):
    resp = client.get("/api/ready")
    assert resp.status_code == 200
    assert resp.json()["database"] == "ok"
    assert resp.json()["storage_ok"] is True
    assert resp.json()["redis_ok"] is True


def test_unauthenticated(client):
    client.cookies.clear()
    assert client.get("/api/projects").status_code == 401


def test_login_and_me(client):
    resp = client.post("/api/auth/dev-login", json={"name": "designer"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "designer"
    assert client.get("/api/me", headers=headers("designer")).json()["name"] == "designer"


def test_create_project_and_drawing(client):
    project = client.post("/api/projects", json={"name": "测试项目"}, headers=headers("admin"))
    assert project.status_code == 201
    pid = project.json()["id"]
    users = client.get("/api/users", headers=headers("admin")).json()
    designer_id = next(u["id"] for u in users if u["name"] == "designer")
    member = client.post(
        f"/api/projects/{pid}/members",
        json={"user_id": designer_id},
        headers=headers("admin"),
    )
    assert member.status_code == 201

    drawing = client.post(
        "/api/drawings",
        json={"project_id": pid, "drawing_no": "SW-2026-001", "title": "安装板"},
        headers=headers("designer"),
    )
    assert drawing.status_code == 201
    assert drawing.json()["status"] == "draft"

    duplicate = client.post(
        "/api/drawings",
        json={"project_id": pid, "drawing_no": "SW-2026-001", "title": "重复"},
        headers=headers("designer"),
    )
    assert duplicate.status_code == 400


def test_generate_and_approve(client):
    project_id = client.get("/api/projects", headers=headers("admin")).json()[0]["id"]
    drawing = client.post(
        "/api/drawings",
        json={"project_id": project_id, "drawing_no": "SW-2026-002", "title": "传感器安装板"},
        headers=headers("designer"),
    ).json()
    drawing_id = drawing["id"]

    payload = {
        "length": 180,
        "width": 120,
        "thickness": 6,
        "material": "304",
        "surface": "拉丝",
        "holes": [
            {"x": 20, "y": 20, "d": 6.6},
            {"x": 160, "y": 20, "d": 6.6},
            {"x": 20, "y": 100, "d": 6.6},
            {"x": 160, "y": 100, "d": 6.6},
        ],
    }
    gen = client.post(f"/api/drawings/{drawing_id}/generate", json=payload, headers=headers("designer"))
    assert gen.status_code == 200
    job_id = gen.json()["job_id"]

    job = client.get(f"/api/jobs/{job_id}", headers=headers("designer")).json()
    assert job["status"] == "done", job

    versions = client.get(f"/api/drawings/{drawing_id}/versions", headers=headers("designer")).json()
    assert len(versions) == 1
    version_id = versions[0]["id"]

    preview = client.get(f"/api/versions/{version_id}/preview", headers=headers("designer"))
    assert preview.status_code == 200
    assert preview.headers["content-type"].startswith("image/png")

    download = client.get(f"/api/versions/{version_id}/download", headers=headers("designer"))
    assert download.status_code == 200

    approved = client.post(
        f"/api/versions/{version_id}/approve", json={"comment": "ok"}, headers=headers("reviewer")
    )
    assert approved.status_code == 200
    detail = client.get(f"/api/drawings/{drawing_id}", headers=headers("designer")).json()
    assert detail["status"] == "approved"

    audit = client.get("/api/audit", params={"object_id": "SW-2026-002"}, headers=headers("admin"))
    assert audit.status_code == 200
    assert any(item["action"] == "version.approve" for item in audit.json())
