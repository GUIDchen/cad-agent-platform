from .conftest import headers


def _users(client):
    return {u["name"]: u for u in client.get("/api/users", headers=headers("admin")).json()}


def test_non_member_isolated(client):
    admin = headers("admin")
    project = client.post("/api/projects", json={"name": "隔离项目"}, headers=admin).json()

    mine = client.get("/api/projects", headers=headers("designer")).json()
    assert all(p["id"] != project["id"] for p in mine)
    assert client.get(f"/api/projects/{project['id']}/members", headers=headers("designer")).status_code == 404


def test_add_member_grants_access(client):
    admin = headers("admin")
    designer = headers("designer")
    project = client.post("/api/projects", json={"name": "成员项目"}, headers=admin).json()
    users = _users(client)

    added = client.post(
        f"/api/projects/{project['id']}/members",
        json={"user_id": users["designer"]["id"]},
        headers=admin,
    )
    assert added.status_code == 201

    mine = client.get("/api/projects", headers=designer).json()
    assert any(p["id"] == project["id"] for p in mine)
    members = client.get(f"/api/projects/{project['id']}/members", headers=designer).json()
    assert any(m["user_name"] == "designer" for m in members)
    drawing = client.post(
        "/api/drawings",
        json={"project_id": project["id"], "drawing_no": "SW-2026-401", "title": "成员图"},
        headers=designer,
    )
    assert drawing.status_code == 201


def test_only_admin_or_owner_adds(client):
    designer = headers("designer")
    designer2 = headers("designer2")
    users = _users(client)

    project = client.post("/api/projects", json={"name": "负责人项目"}, headers=designer).json()
    assert (
        client.post(
            f"/api/projects/{project['id']}/members",
            json={"user_id": users["designer2"]["id"]},
            headers=designer,
        ).status_code
        == 201
    )
    assert (
        client.post(
            f"/api/projects/{project['id']}/members",
            json={"user_id": users["viewer"]["id"]},
            headers=designer2,
        ).status_code
        == 403
    )
    assert client.post("/api/projects", json={"name": "普通查看者项目"}, headers=headers("viewer")).status_code == 403


def test_member_change_notifies(client, tmp_path, monkeypatch):
    monkeypatch.setenv("NOTIFY_MODE", "mock")
    monkeypatch.setenv("NOTIFY_LOG", str(tmp_path / "notify.log"))
    admin = headers("admin")
    project = client.post("/api/projects", json={"name": "通知项目"}, headers=admin).json()
    users = _users(client)
    client.post(
        f"/api/projects/{project['id']}/members",
        json={"user_id": users["designer"]["id"]},
        headers=admin,
    )
    text = (tmp_path / "notify.log").read_text(encoding="utf-8")
    assert "项目成员" in text
    assert "designer" in text


def test_remove_owner_forbidden(client):
    admin = headers("admin")
    project = client.post("/api/projects", json={"name": "负责人项目2"}, headers=admin).json()
    users = _users(client)
    resp = client.delete(
        f"/api/projects/{project['id']}/members/{users['admin']['id']}",
        headers=admin,
    )
    assert resp.status_code == 400


def test_update_member_role(client):
    designer = headers("designer")
    users = _users(client)
    project = client.post("/api/projects", json={"name": "角色项目"}, headers=designer).json()
    assert client.post(
        f"/api/projects/{project['id']}/members",
        json={"user_id": users["designer2"]["id"]},
        headers=designer,
    ).status_code == 201

    resp = client.patch(
        f"/api/projects/{project['id']}/members/{users['designer2']['id']}",
        json={"role": "owner"},
        headers=designer,
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "owner"

    owner_demote = client.patch(
        f"/api/projects/{project['id']}/members/{users['designer']['id']}",
        json={"role": "member"},
        headers=designer,
    )
    assert owner_demote.status_code == 400
